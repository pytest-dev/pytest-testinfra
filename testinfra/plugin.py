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

import logging

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
User = modules.User.as_fixture()
Salt = modules.Salt.as_fixture()
PuppetResource = modules.PuppetResource.as_fixture()
Facter = modules.Facter.as_fixture()
Sysctl = modules.Sysctl.as_fixture()
Socket = modules.Socket.as_fixture()
Ansible = modules.Ansible.as_fixture()
Process = modules.Process.as_fixture()


@pytest.fixture(scope="module")
def LocalCommand(testinfra_backend):
    """Run commands locally

    Same as `Command` but run commands locally with subprocess even
    when the connection backend is not "local".

    Note: `LocalCommand` does NOT respect ``--sudo`` option
    """
    return testinfra.get_backend("local://").get_module("Command")


def pytest_addoption(parser):
    group = parser.getgroup("testinfra")
    group._addoption(
        "--connection",
        action="store",
        dest="connection",
        help=(
            "Remote connection backend (paramiko, ssh, safe-ssh, "
            "salt, docker, ansible)"
        )
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
        "--ansible-inventory",
        action="store",
        dest="ansible_inventory",
        help="Ansible inventory file",
    )
    group._addoption(
        "--nagios",
        action="store_true",
        dest="nagios",
        help="Nagios plugin",
    )


def pytest_generate_tests(metafunc):
    if "testinfra_backend" in metafunc.fixturenames:
        if metafunc.config.option.hosts is not None:
            hosts = metafunc.config.option.hosts.split(",")
        elif hasattr(metafunc.module, "testinfra_hosts"):
            hosts = metafunc.module.testinfra_hosts
        else:
            hosts = [None]
        params = testinfra.get_backends(
            hosts,
            connection=metafunc.config.option.connection,
            ssh_config=metafunc.config.option.ssh_config,
            sudo=metafunc.config.option.sudo,
            ansible_inventory=metafunc.config.option.ansible_inventory,
        )
        ids = [e.get_pytest_id() for e in params]
        metafunc.parametrize(
            "testinfra_backend", params, ids=ids, scope="module")


def pytest_configure(config):
    if config.option.verbose > 0:
        logging.basicConfig()
        logging.getLogger("testinfra").setLevel(logging.DEBUG)
