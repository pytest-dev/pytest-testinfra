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

from testinfra import get_system_info
from testinfra.modules.base import Module


class Interface(Module):
    """Test network interfaces"""

    def __init__(self, name):
        self.name = name
        super(Interface, self).__init__()

    @property
    def exists(self):
        raise NotImplementedError

    def __repr__(self):
        return "<interface %s>" % (self.name,)

    @classmethod
    def as_fixture(cls):
        @pytest.fixture(scope="session")
        def f():
            if get_system_info().type == "linux":
                return LinuxInterface
            else:
                raise NotImplementedError
        f.__doc__ = cls.__doc__
        return f


class LinuxInterface(Interface):

    @property
    def exists(self):
        return self.run_test("ip link show %s", self.name).rc == 0

    @property
    def speed(self):
        return int(self.check_output(
            "cat /sys/class/net/%s/speed", self.name))

    @property
    def addresses(self):
        stdout = self.check_output("ip addr show %s", self.name)
        addrs = []
        for line in stdout.splitlines():
            splitted = [e.strip() for e in line.split(" ") if e]
            if splitted and splitted[0] in ("inet", "inet6"):
                addrs.append(splitted[1].split("/", 1)[0])
        return addrs
