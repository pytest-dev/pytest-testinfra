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


class _AddrPort(object):
    def __init__(self, addr, port):
        self._addr = addr
        self._port = str(port)

    @property
    def is_reachable(self):
        if not self._has_netcat:
            # Fallback to bash if netcat is not available
            return self._addr.run(
                "timeout 1 bash -c 'cat < /dev/null > /dev/tcp/%s/%s'",
                self._addr.name, self._port).rc == 0

        return self._addr.run(
            "nc -w 1 -z %s %s", self._addr.name, self._port).rc == 0

    @property
    def _has_netcat(self):
        return self._addr.run("command -v nc").rc == 0


class Addr(Module):
    """Test remote address

    Example:

    >>> google = host.addr("google.com")
    >>> google.is_resolvable
    True
    >>> '173.194.32.225' in google.ipv4_addresses
    True
    >>> google.is_reachable
    True
    >>> google.port(443).is_reachable
    True
    >>> google.port(666).is_reachable
    False
    """

    def __init__(self, name):
        self._name = name
        super(Addr, self).__init__()

    @property
    def name(self):
        """Return host name"""
        return self._name

    @property
    def is_resolvable(self):
        """Return if address is resolvable"""
        return self.run("getent ahosts %s", self.name).rc == 0

    @property
    def is_reachable(self):
        """Return if address is reachable"""
        if self.run("command -v ping").rc != 0:
            raise RuntimeError("Command 'ping' not available")

        return self.run("ping -W 1 -c 1 %s", self.name).rc == 0

    @property
    def ip_addresses(self):
        """Return IP addresses of host"""
        return self._resolve("ahosts")

    @property
    def ipv4_addresses(self):
        """Return IPv4 addresses of host"""
        return self._resolve("ahostsv4")

    @property
    def ipv6_addresses(self):
        """Return IPv6 addresses of host"""
        return self._resolve("ahostsv6")

    def port(self, port):
        """Return address-port pair"""
        return _AddrPort(self, port)

    @classmethod
    def get_module_class(cls, host):
        return super(Addr, cls).get_module_class(host)

    def __repr__(self):
        return "<addr %s>" % (self.name,)

    def _resolve(self, method):
        result = self.run("getent %s %s", method, self.name)
        if result.rc != 0:
            return []
        lines = result.stdout.splitlines()
        return list(set(line.split()[0] for line in lines))
