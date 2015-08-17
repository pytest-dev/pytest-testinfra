# -*- coding: utf8 -*-
# Copyright © 2015 Philippe Pepiot
#
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

from __future__ import unicode_literals

import pytest
from six.moves import urllib
import testinfra
from testinfra import modules

File = modules.File.as_fixture()
Command = modules.Command.as_fixture()
Package = modules.Package.as_fixture()
Group = modules.Group.as_fixture()
Interface = modules.Interface.as_fixture()
Command = modules.Command.as_fixture()
Service = modules.Service.as_fixture()
SystemInfo = modules.SystemInfo.as_fixture()
User = modules.User.as_fixture()
Salt = modules.Salt.as_fixture()
PuppetResource = modules.PuppetResource.as_fixture()
Facter = modules.Facter.as_fixture()
Sysctl = modules.Sysctl.as_fixture()


@pytest.fixture(scope="module")
def _testinfra_backend(request, pytestconfig, _testinfra_host):
    kwargs = {}
    if pytestconfig.option.ssh_config is not None:
        kwargs["ssh_config"] = pytestconfig.option.ssh_config
    if pytestconfig.option.sudo is not None:
        kwargs["sudo"] = pytestconfig.option.sudo
    if _testinfra_host is not None:
        if "://" in _testinfra_host:
            url = urllib.parse.urlparse(_testinfra_host)
            backend_type = url.scheme
            host = url.netloc
            query = urllib.parse.parse_qs(url.query)
            if query.get("sudo", ["false"])[0].lower() == "true":
                kwargs["sudo"] = True
            if "ssh_config" in query:
                kwargs["ssh_config"] = query.get("ssh_config")[0]
        else:
            backend_type = pytestconfig.option.connection or "paramiko"
            host = _testinfra_host
        backend = testinfra.get_backend(
            backend_type,
            host,
            **kwargs)
    else:
        backend = testinfra.get_backend("local", **kwargs)
    return backend


@pytest.fixture(scope="module")
def LocalCommand():
    return testinfra.get_backend("local").get_module("Command")


def pytest_addoption(parser):
    group = parser.getgroup("testinfra")
    group._addoption(
        "--connection",
        action="store",
        dest="connection",
        help="Remote connection backend paramiko|ssh|safe-ssh|salt|docker",
    )
    group._addoption(
        "--hosts",
        action="store",
        dest="hosts",
        help="Hosts list (comma separated)",
    )
    group._addoption(
        "--ssh-config",
        action="store",
        dest="ssh_config",
        help="SSH config file",
    )
    group._addoption(
        "--sudo",
        action="store_true",
        dest="sudo",
        help="Use sudo",
    )
    group._addoption(
        "--nagios",
        action="store_true",
        dest="nagios",
        help="Nagios plugin",
    )


def pytest_generate_tests(metafunc):
    if "_testinfra_host" in metafunc.fixturenames:
        if (metafunc.config.option.hosts == "*" and
                metafunc.config.option.connection == "salt"):
            import salt.runner
            opts = salt.config.master_config("/etc/salt/master")
            runner = salt.runner.RunnerClient(opts)
            minions_list = runner.cmd("manage.up", [])
            metafunc.config.option.hosts = ",".join(minions_list)
        if metafunc.config.option.hosts is not None:
            params = metafunc.config.option.hosts.split(",")
            ids = params
        elif hasattr(metafunc.module, "testinfra_hosts"):
            params = metafunc.module.testinfra_hosts
            ids = params
        else:
            params = [None]
            ids = ["local"]
        metafunc.parametrize(
            "_testinfra_host", params, ids=ids, scope="module")
