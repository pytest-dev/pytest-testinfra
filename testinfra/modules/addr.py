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


class Addr(Module):
    """Test remote address

    If port is not supplied test host availability using ping
    If protocol is not supplied assume it TCP if port is supplied
    """

    def __init__(self, name, port=None, proto=None):
        self._name = name
        self._port = port
        self._proto = proto
        super(Addr, self).__init__()

    @property
    def name(self):
        """Return host name"""
        return self._name

    @property
    def port(self):
        """Return host port"""
        return self._port

    @property
    def proto(self):
        """Return host protocol"""
        if self._proto is None:
            if self._port is None:
                return 'icmp'
            return 'tcp'
        return self._proto

    @property
    def is_resolvable(self):
        """Return if address is resolvable"""
        return self.run("getent ahosts %s", self.name).rc == 0

    @property
    def is_reachable(self):
        """Return if address is resolvable"""
        if self.proto == 'icmp':
            return self.run("ping -c 1 %s", self.name).rc == 0
        if self.proto == 'tcp':
            addr = self.ipv4_address
            if addr is None:
                return False
            return self.run("nc -w 10 -nz %s %s", addr, self.port).rc == 0
        return False

    @property
    def ipv4_address(self):
        result = self.run("getent ahostsv4 %s | awk '{print $1; exit}'", self.name)
        if result.rc != 0:
            return None
        return result.stdout

    @classmethod
    def get_module_class(cls, host):
        return super(Addr, cls).get_module_class(host)

    def __repr__(self):
        return "<addr %s>" % (self.name,)
