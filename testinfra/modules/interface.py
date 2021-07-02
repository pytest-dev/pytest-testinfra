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

from testinfra.modules.base import Module
from testinfra.utils import cached_property


class Interface(Module):
    """Test network interfaces

    >>> host.interface("eth0").exists
    True

    Optionally, the protocol family to use can be enforced.

    >>> host.interface("eth0", "inet6").addresses
    ['fe80::e291:f5ff:fe98:6b8c']
    """

    def __init__(self, name, family=None):
        self.name = name
        self.family = family
        super().__init__()

    @property
    def exists(self):
        raise NotImplementedError

    @property
    def speed(self):
        raise NotImplementedError

    @property
    def addresses(self):
        """Return ipv4 and ipv6 addresses on the interface

        >>> host.interface("eth0").addresses
        ['192.168.31.254', '192.168.31.252', 'fe80::e291:f5ff:fe98:6b8c']
        """
        raise NotImplementedError

    def __repr__(self):
        return "<interface {}>".format(self.name)

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            return LinuxInterface
        if host.system_info.type.endswith("bsd"):
            return BSDInterface
        raise NotImplementedError

    @classmethod
    def names(cls):
        """Return the names of all the interfaces.

        >>> host.interface.names()
        ['lo', 'tunl0', 'ip6tnl0', 'eth0']
        """
        raise NotImplementedError

    @classmethod
    def default(cls, family=None):
        """Return the interface used for the default route.

        >>> host.interface.default()
        <interface eth0>

        Optionally, the protocol family to use can be enforced.

        >>> host.interface.default("inet6")
        None
        """
        raise NotImplementedError


class LinuxInterface(Interface):
    @cached_property
    def _ip(self):
        ip_cmd = self.find_command("ip")
        if self.family is not None:
            ip_cmd = f"{ip_cmd} -f {self.family}"
        return ip_cmd

    @property
    def exists(self):
        return self.run_test("{} link show %s".format(self._ip), self.name).rc == 0

    @property
    def speed(self):
        return int(self.check_output("cat /sys/class/net/%s/speed", self.name))

    @property
    def addresses(self):
        stdout = self.check_output("{} addr show %s".format(self._ip), self.name)
        addrs = []
        for line in stdout.splitlines():
            splitted = [e.strip() for e in line.split(" ") if e]
            if splitted and splitted[0] in ("inet", "inet6"):
                addrs.append(splitted[1].split("/", 1)[0])
        return addrs

    @classmethod
    def default(cls, family=None):
        _default = cls(None, family=family)
        out = cls.check_output("{} route ls".format(_default._ip))
        for line in out.splitlines():
            if "default" in line:
                _default.name = line.strip().rsplit(" ", 1)[-1]
        return _default

    @classmethod
    def names(cls):
        # -o is to tell the ip command to return 1 line per interface
        out = cls.check_output("{} -o link show".format(cls(None)._ip))
        interfaces = []
        for line in out.splitlines():
            interfaces.append(line.strip().split(": ", 2)[1].split("@", 1)[0])
        return interfaces


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
