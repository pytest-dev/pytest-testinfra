# -*- coding: utf-8 -*-
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

import argparse

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


class ArgumentParserAsPyTestConfigOptionGroup(object):
    """
    This is an ugly hack, since py.test does not allow for plugin to only print
    it's help in any easy way.

    Mock up ArgumentParser parser as pytest.config.OptionGroup which allows
    would allow us to create a register argument options for this parser
    using py.tests' pytest_addoption construct. Then by specifying
    add_help=True we force the parser to print only plugin help when
    parse_known_args is called, since parse_known_args exits script after
    showing help.
    """

    def __init__(self):
        # create parse and set add_help so we
        self.parser = argparse.ArgumentParser(add_help=True)
        # add py.test options
        pytest_addoption(self)

    def parse_known_args(self, *args, **kwargs):
        """
        Return result of ArgumentParser.parse_known_args
        to it.
        """
        return self.parser.parse_known_args(*args, **kwargs)

    def getgroup(self, *args, **kwargs):
        """
        Expose getgroup to mock pytest.config.OptionGroup.getgroup
        Return own instance as the "fake" group
        """
        return self

    def _addoption(self, *args, **kwargs):
        """
        Expose _addoption method to mock pytest.config.OptionGroup._addoption
        call ArgumentParser parser with method arguments to create script
        argument
        """
        self.parser.add_argument(*args, **kwargs)


def _get_testinfra_hosts():
    # It would be better to use pytest_generate_tests but it doesn't play well
    # with pytest.mark.parametrize().
    # See https://github.com/pytest-dev/pytest/issues/896
    # This is a ugly working workaround
    parser = ArgumentParserAsPyTestConfigOptionGroup()
    known_args, _ = parser.parse_known_args()
    if known_args.hosts is None:
        params = [None]
        ids = ["local"]
    else:
        params = known_args.hosts.split(",")
        ids = params
    return {
        "params": params,
        "ids": ids,
    }


@pytest.fixture(scope="session", **_get_testinfra_hosts())
def testinfra_backend(request, pytestconfig):
    kwargs = {}
    if pytestconfig.option.ssh_config is not None:
        kwargs["ssh_config"] = pytestconfig.option.ssh_config
    if pytestconfig.option.sudo is not None:
        kwargs["sudo"] = pytestconfig.option.sudo
    if request.param is not None:
        backend_type = pytestconfig.option.connection or "paramiko"
        testinfra.set_backend(
            backend_type,
            request.param,
            **kwargs)
    else:
        testinfra.set_backend("local", **kwargs)

