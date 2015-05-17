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


@pytest.fixture(scope="session")
def testinfra_backend(pytestconfig, _testinfra_host):
    if _testinfra_host is not None:
        backend_type = pytestconfig.option.connection or "paramiko"
        kwargs = {}
        if pytestconfig.option.ssh_config is not None:
            kwargs["ssh_config"] = pytestconfig.option.ssh_config
        testinfra.set_backend(
            backend_type,
            _testinfra_host,
            **kwargs)
    else:
        testinfra.set_backend("local")


def pytest_addoption(parser):
    group = parser.getgroup("testinfra")
    group._addoption(
        "--connection",
        action="store",
        dest="connection",
        help="Remote connection backend paramiko|ssh|safe_ssh|salt",
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
        "--nagios",
        action="store_true",
        dest="nagios",
        help="Nagios plugin",
    )


def pytest_generate_tests(metafunc):
    if "_testinfra_host" in metafunc.fixturenames:
        if metafunc.config.option.hosts is not None:
            params = metafunc.config.option.hosts.split(",")
            ids = params
        elif hasattr(metafunc.module, "hosts"):
            params = metafunc.module.hosts
            ids = params
        else:
            params = [None]
            ids = ["local"]
        metafunc.parametrize(
            "_testinfra_host", params, ids=ids, scope="session")
