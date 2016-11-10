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
Supervisor = modules.Supervisor.as_fixture()
MountPoint = modules.MountPoint.as_fixture()
Sudo = modules.Sudo.as_fixture()
PipPackage = modules.PipPackage.as_fixture()


@pytest.fixture()
def LocalCommand(TestinfraBackend):
    """Run commands locally

    Same as `Command` but run commands locally with subprocess even
    when the connection backend is not "local".

    Note: `LocalCommand` does NOT respect ``--sudo`` option
    """
    return testinfra.get_backend("local://").get_module("Command")


@pytest.fixture(scope="module")
def TestinfraBackend(_testinfra_backend):
    return _testinfra_backend


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
    if "_testinfra_backend" in metafunc.fixturenames:
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
            sudo_user=metafunc.config.option.sudo_user,
            ansible_inventory=metafunc.config.option.ansible_inventory,
        )
        ids = [e.get_pytest_id() for e in params]
        metafunc.parametrize(
            "_testinfra_backend", params, ids=ids, scope="module")


def pytest_configure(config):
    if config.option.verbose > 1:
        logging.basicConfig()
        logging.getLogger("testinfra").setLevel(logging.DEBUG)
