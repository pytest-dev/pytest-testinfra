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
            if self._has_netcat:
                return self.run(
                    "timeout 5 nc -z %s %s", self.name, str(self.port)).rc == 0
            # Try to fallback to bash if netcat is not installed
            return self.run(
                "timeout 5 bash -c 'cat < /dev/null > /dev/tcp/%s/%s'",
                self.name, str(self.port)).rc == 0
        return False

    @classmethod
    def get_module_class(cls, host):
        return super(Addr, cls).get_module_class(host)

    def __repr__(self):
        return "<addr %s>" % (self.name,)

    @property
    def _has_netcat(self):
        return self.run("command -v nc").rc == 0
