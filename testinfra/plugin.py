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

import logging
import shutil
import sys
import tempfile
import time

import pytest

import testinfra
import testinfra.host
import testinfra.modules


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
            "salt, docker, ansible, podman)"
        ),
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
        "--force-ansible",
        action="store_true",
        dest="force_ansible",
        help=(
            "Force use of ansible connection backend only (slower but all "
            "ansible connection options are handled)"
        ),
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
            force_ansible=metafunc.config.option.force_ansible,
        )
        params = sorted(params, key=lambda x: x.backend.get_pytest_id())
        ids = [e.backend.get_pytest_id() for e in params]
        metafunc.parametrize(
            "_testinfra_host", params, ids=ids, scope="module", indirect=True
        )


class NagiosReporter:
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
            status = b"CRITICAL"
            ret = 2
        else:
            status = b"OK"
            ret = 0

        out = sys.stdout.buffer
        out.write(
            (b"TESTINFRA %s - %d passed, %d failed, %d skipped in %.2f " b"seconds\n")
            % (
                status,
                self.passed,
                self.failed,
                self.skipped,
                time.time() - self.start_time,
            )
        )
        self.out.seek(0)
        shutil.copyfileobj(self.out, out)
        return ret


class SpooledTemporaryFile(tempfile.SpooledTemporaryFile):
    def __init__(self, *args, **kwargs):
        if "b" in kwargs.get("mode", "b"):
            self._out_encoding = kwargs.pop("encoding")
        else:
            self._out_encoding = kwargs.get("encoding")
        super().__init__(*args, **kwargs)

    def write(self, s):
        # avoid traceback in py.io.terminalwriter.write_out
        # TypeError: a bytes-like object is required, not 'str'
        if isinstance(s, str):
            s = s.encode(self._out_encoding)
        return super().write(s)


@pytest.mark.trylast
def pytest_configure(config):
    if config.getoption("--verbose", 0) > 1:
        root = logging.getLogger()
        if not root.handlers:
            root.addHandler(logging.NullHandler())
        logging.getLogger("testinfra").setLevel(logging.DEBUG)
    if config.getoption("--nagios"):
        # disable & re-enable terminalreporter to write in a tempfile
        reporter = config.pluginmanager.getplugin("terminalreporter")
        if reporter:
            out = SpooledTemporaryFile(encoding=sys.stdout.encoding)
            config.pluginmanager.unregister(reporter)
            reporter = reporter.__class__(config, out)
            config.pluginmanager.register(reporter, "terminalreporter")
            config.pluginmanager.register(NagiosReporter(out), "nagiosreporter")


@pytest.mark.trylast
def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.getplugin("nagiosreporter")
    if reporter:
        session.exitstatus = reporter.report()
