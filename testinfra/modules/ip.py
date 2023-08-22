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

import functools
import json
import re

from testinfra.modules.base import Module

class IP(Module):
    """Test network configuration via ip commands

    >>> host.ip.rules()

    host.ip.rules(from,to,tos,fwmark,iif,oif,pref, uidrange, ipproto, sport, dport)
    host.ip.routes(table, device, scope, proto, src, metric)
    host.ip.links()
    host.ip.addresses()
    host.ip.tunnels()

    Optionally, the protocol family can be provided:
    >>> host.ip.routes("inet6", table="main")
    ...FIX

    Optionally, this can work inside a different network namespace:
    >>> host.ip.routes("inet6", "vpn")
    ...FIX
    """

    def __init__(self, family=None, netns=None):
        self.family = family
        self.netns = netns
        super().__init__()

    @property
    def exists(self):
        raise NotImplementedError

    def addresses(self):
        """Return the addresses associated with interfaces
        """
        raise NotImplementedError

    def links(self):
        """Return links and their state
        """
        raise NotImplementedError

    def routes(self):
        """Return the routes associated with the routing table
        """
        raise NotImplementedError

    def rules(self):
        """Return all configured ip rules
        """
        raise NotImplementedError

    def tunnels(self):
        """Return all configured tunnels
        """
        raise NotImplementedError

    def __repr__(self):
        return "<ip>"

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            return LinuxIP
        raise NotImplementedError

class LinuxIP(IP):
    @functools.cached_property
    def _ip(self):
        ip_cmd = self.find_command("ip")
        if self.netns is not None:
            ip_cmd = f"{ip_cmd} netns exec {self.netns} {ip_cmd}"
        if self.family is not None:
            ip_cmd = f"{ip_cmd} -f {self.family}"
        return ip_cmd

    @property
    def exists(self):
        return self.run_test("{} -V".format(self._ip), self.name).rc == 0

    def addresses(self):
        """Return the addresses associated with interfaces
        """
        cmd = f"{self._ip} --json address show"
        out = self.check_output(cmd)
        return json.loads(out)

    def links(self):
        """Return links and their state
        """
        cmd = f"{self._ip} --json link show"
        out = self.check_output(cmd)
        return json.loads(out)

    def routes(self):
        """Return the routes installed
        """
        cmd = f"{self._ip} --json route show table all"
        out = self.check_output(cmd)
        return json.loads(out)

    def rules(self):
        """Return the rules our routing policy consists of
        """
        cmd = f"{self._ip} --json rule show"
        out = self.check_output(cmd)
        return json.loads(out)

    def tunnels(self):
        """Return all configured tunnels
        """
        cmd = f"{self._ip} --json tunnel show"
        out = self.check_output(cmd)
        return json.loads(out)
