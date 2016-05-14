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

from __future__ import unicode_literals

from testinfra.modules.base import Module


class Interface(Module):
    """Test network interfaces"""

    def __init__(self, name):
        self.name = name
        super(Interface, self).__init__()

    @property
    def exists(self):
        raise NotImplementedError

    @property
    def speed(self):
        raise NotImplementedError

    @property
    def addresses(self):
        """Return ipv4 and ipv6 addresses on the interface

        >>> Interface("eth0").addresses
        ['192.168.31.254', '192.168.31.252', 'fe80::e291:f5ff:fe98:6b8c']
        """
        raise NotImplementedError

    def __repr__(self):
        return "<interface %s>" % (self.name,)

    @classmethod
    def get_module_class(cls, _backend):
        SystemInfo = _backend.get_module("SystemInfo")
        if SystemInfo.type == "linux":
            return LinuxInterface
        elif SystemInfo.type.endswith("bsd"):
            return BSDInterface
        else:
            raise NotImplementedError


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


class BSDInterface(Interface):

    @property
    def exists(self):
        return self.run_test("ifconfig %s", self.name).rc == 0

    @property
    def speed(self):
        raise NotImplementedError

    @property
    def addresses(self):
        stdout = self.check_output("ifconfig %s", self.name)
        addrs = []
        for line in stdout.splitlines():
            if line.startswith("\tinet "):
                addrs.append(line.split(" ", 2)[1])
            elif line.startswith("\tinet6 "):
                addr = line.split(" ", 2)[1]
                if "%" in addr:
                    addr = addr.split("%", 1)[0]
                addrs.append(addr)
        return addrs
