# coding: utf-8
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=redefined-outer-name

from __future__ import unicode_literals

import logging
import shutil
import sys
import tempfile
import time
import warnings

import pytest
import six
import testinfra
import testinfra.host
import testinfra.modules
import testinfra.utils as utils


def _generate_fixtures():
    self = sys.modules[__name__]
    for modname in testinfra.modules.modules:
        modname = modname.title().replace("_", "")

        def get_fixture(name):
            new_name = utils.un_camel_case(name)

            @pytest.fixture()
            def f(TestinfraBackend):
                # pylint: disable=protected-access
                return getattr(TestinfraBackend._host, new_name)
            f.__name__ = str(name)
            f.__doc__ = ('DEPRECATED: use host fixture and get {0} module '
                         'with host.{1}').format(name, new_name)
            return f
        setattr(self, modname, get_fixture(modname))


_generate_fixtures()


@pytest.fixture()
def LocalCommand(request, TestinfraBackend):
    """DEPRECATED

    Use host fixture and get LocalCommand with host.get_host("local://")
    """
    # pylint: disable=protected-access
    return TestinfraBackend._host.get_host("local://")


@pytest.fixture()
def TestinfraBackend(host):
    "DEPRECATED: use host fixture and get TestinfraBackend with host.backend"
    return host.backend


@pytest.fixture(scope="module")
def _testinfra_host(request):
    return request.param


@pytest.fixture(scope="module")
def host(_testinfra_host):
    return _testinfra_host


host.__doc__ = testinfra.host.Host.__doc__


def pytest_addoption(parser):
    group = parser.getgroup("testinfra")
    group.addoption(
        "--connection",
        action="store",
        dest="connection",
        help=(
            "Remote connection backend (paramiko, ssh, safe-ssh, "
            "salt, docker, ansible)"
        )
    )
    group.addoption(
        "--hosts",
        action="store",
        dest="hosts",
        help="Hosts list (comma separated)",
    )
    group.addoption(
        "--ssh-config",
        action="store",
        dest="ssh_config",
        help="SSH config file",
    )
    group.addoption(
        "--ssh-identity-file",
        action="store",
        dest="ssh_identity_file",
        help="SSH identify file",
    )
    group.addoption(
        "--sudo",
        action="store_true",
        dest="sudo",
        help="Use sudo",
    )
    group.addoption(
        "--sudo-user",
        action="store",
        dest="sudo_user",
        help="sudo user",
    )
    group.addoption(
        "--ansible-inventory",
        action="store",
        dest="ansible_inventory",
        help="Ansible inventory file",
    )
    group.addoption(
        "--nagios",
        action="store_true",
        dest="nagios",
        help="Nagios plugin",
    )


def pytest_generate_tests(metafunc):
    if "_testinfra_host" in metafunc.fixturenames:
        if metafunc.config.option.hosts is not None:
            hosts = metafunc.config.option.hosts.split(",")
        elif hasattr(metafunc.module, "testinfra_hosts"):
            hosts = metafunc.module.testinfra_hosts
        else:
            hosts = [None]
        params = testinfra.get_hosts(
            hosts,
            connection=metafunc.config.option.connection,
            ssh_config=metafunc.config.option.ssh_config,
            ssh_identity_file=metafunc.config.option.ssh_identity_file,
            sudo=metafunc.config.option.sudo,
            sudo_user=metafunc.config.option.sudo_user,
            ansible_inventory=metafunc.config.option.ansible_inventory,
        )
        params = sorted(params, key=lambda x: x.backend.get_pytest_id())
        ids = [e.backend.get_pytest_id() for e in params]
        metafunc.parametrize(
            "_testinfra_host", params, ids=ids, scope="module", indirect=True)


def pytest_collection_finish(session):
    deprecated_modules = set(
        m.title().replace("_", "") for m in testinfra.modules.modules) | set(
            ['TestinfraBackend', 'LocalCommand'])
    deprecated_used = set()
    for item in session.items:
        if hasattr(item, 'fixturenames'):
            # DoctestItem does not have fixturenames attribute
            deprecated_used |= (set(item.fixturenames) & deprecated_modules)
    for name in sorted(deprecated_used):
        if name == 'LocalCommand':
            msg = ("LocalCommand fixture is deprecated. Use host fixture "
                   "and get LocalCommand with host.get_host('local://')")
        elif name == 'TestinfraBackend':
            msg = ("TestinfraBackend fixture is deprecated. Use host fixture "
                   "and get backend with host.backend")
        elif name == 'Command':
            msg = "Command fixture is deprecated. Use host fixture instead"
        else:
            msg = (
                "{0} fixture is deprecated. Use host fixture and get "
                "{0} module with host.{1}"
            ).format(name, utils.un_camel_case(name))
        warnings.warn(msg, DeprecationWarning)


class NagiosReporter(object):

    def __init__(self, out):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = time.time()
        self.total_time = None
        self.out = out

    def pytest_runtest_logreport(self, report):
        if report.passed:
            if report.when == "call":  # ignore setup/teardown
                self.passed += 1
        elif report.failed:
            self.failed += 1
        elif report.skipped:
            self.skipped += 1

    def report(self):
        if self.failed:
            status = b'CRITICAL'
            ret = 2
        else:
            status = b'OK'
            ret = 0

        if hasattr(sys.stdout, 'buffer'):
            out = sys.stdout.buffer
        else:
            out = sys.stdout

        out.write((
            b"TESTINFRA %s - %d passed, %d failed, %d skipped in %.2f "
            b"seconds\n") % (
                status, self.passed, self.failed, self.skipped,
                time.time() - self.start_time))
        self.out.seek(0)
        shutil.copyfileobj(self.out, out)
        return ret


if six.PY2:
    class SpooledTemporaryFile(tempfile.SpooledTemporaryFile):

        def __init__(self, encoding=None, *args, **kwargs):
            # tempfile.SpooledTemporaryFile is not new style class
            tempfile.SpooledTemporaryFile.__init__(self, *args, **kwargs)
            self.encoding = encoding
else:
    class SpooledTemporaryFile(tempfile.SpooledTemporaryFile):

        def __init__(self, *args, **kwargs):
            self._out_encoding = kwargs['encoding']
            super().__init__(*args, **kwargs)

        def write(self, s):
            # avoid traceback in py.io.terminalwriter.write_out
            # TypeError: a bytes-like object is required, not 'str'
            if isinstance(s, str):
                s = s.encode(self._out_encoding)
            return super().write(s)


@pytest.mark.trylast
def pytest_configure(config):
    if config.option.verbose > 1:
        root = logging.getLogger()
        if not root.handlers:
            root.addHandler(logging.NullHandler())
        logging.getLogger("testinfra").setLevel(logging.DEBUG)
    if config.option.nagios:
        # disable & re-enable terminalreporter to write in a tempfile
        reporter = config.pluginmanager.getplugin('terminalreporter')
        if reporter:
            out = SpooledTemporaryFile(encoding=sys.stdout.encoding)
            config.pluginmanager.unregister(reporter)
            reporter = reporter.__class__(config, out)
            config.pluginmanager.register(reporter, 'terminalreporter')
            config.pluginmanager.register(NagiosReporter(out),
                                          'nagiosreporter')


@pytest.mark.trylast
def pytest_unconfigure(config):
    reporter = config.pluginmanager.getplugin('nagiosreporter')
    if reporter:
        sys.exit(reporter.report())
