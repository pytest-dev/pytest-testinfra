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

from testinfra.modules.base import InstanceModule


class IProute2(InstanceModule):
    """Test network configuration via iproute2 commands

        Optional arguments:
        - family: force iproute2 tools to use a specific protocol family
        - namespace: execute iproute2 tools inside the provided namespace

    """

    def __init__(self, family=None, namespace=None):
        self.family = family
        self.namespace = namespace
        super().__init__()

    def __repr__(self):
        return "<ip>"

    @functools.cached_property
    def _ip(self):
        ip_cmd = self.find_command("ip")
        if self.namespace is not None:
            ip_cmd = f"{ip_cmd} -n {self.namespace}"
        if self.family is not None:
            ip_cmd = f"{ip_cmd} -f {self.family}"
        return ip_cmd

    @property
    def exists(self):
        return self.run_test("{} -V".format(self._ip)).rc == 0

    def addresses(self, address=None, ifname=None, local=None):
        """Return the addresses associated with interfaces

            Optionally, results can be filtered by:
            - address
            - ifname
            - local

        """
        cmd = f"{self._ip} --json address show"
        out = self.check_output(cmd)
        j = json.loads(out)
        o = []
        if address is None and ifname is None and local is None:
            # no filters, bail out early
            return j
        if address is not None:
            [o.append(x) for x in j if x["address"] == address]
        if ifname is not None:
            [o.append(x) for x in j if x["ifname"] == ifname]
        if local is not None:
            for x in j:
                for addr in x["addr_info"]:  # multiple IPs in an interface
                    if addr["local"] == local:
                        o.append(x)
        return o

    def links(self):
        """Return links and their state"""
        cmd = f"{self._ip} --json link show"
        out = self.check_output(cmd)
        return json.loads(out)

    def routes(
        self, table="all", device=None, scope=None, proto=None, src=None, metric=None
    ):
        """Returns the routes installed

            Optionally, routes returned can be filtered with the following
            selectors. This can be useful in busy routing tables.

            Selectors:
            - table
            - device (maps to ip-route's 'dev' selector)
            - scope
            - proto
            - src
            - metric

        """
        cmd = f"{self._ip} --json route show "
        options = []
        if table is not None:
            options += ["table", table]
        if device is not None:
            options += ["dev", device]
        if scope is not None:
            options += ["scope", scope]
        if proto is not None:
            options += ["proto", proto]
        if src is not None:
            options += ["src", src]
        if metric is not None:
            options += ["metric", metric]

        cmd += " ".join(options)
        out = self.check_output(cmd)
        return json.loads(out)

    def rules(
        self,
        src=None,
        to=None,
        tos=None,
        fwmark=None,
        iif=None,
        oif=None,
        pref=None,
        uidrange=None,
        ipproto=None,
        sport=None,
        dport=None,
    ):
        """Returns the rules our routing policy consists of

            Optionally, rules returned can be filtered with the following
            selectors. This can be useful in busy rulesets.

            Selectors:
            - src (maps to ip-rule's 'from' selector)
            - to
            - tos
            - fwmark
            - iif
            - oif
            - pref
            - uidrange
            - ipproto
            - sport
            - dport

        """
        cmd = f"{self._ip} --json rule show "

        options = []
        if src is not None:
            options += ["from", src]

        if to is not None:
            options += ["to", to]

        if tos is not None:
            options += ["tos", tos]

        if fwmark is not None:
            options += ["fwmark", fwmark]

        if iif is not None:
            options += ["iif", iif]

        if oif is not None:
            options += ["oif", oif]

        if pref is not None:
            options += ["pref", pref]

        if uidrange is not None:
            options += ["uidrange", uidrange]

        if ipproto is not None:
            options += ["ipproto", ipproto]

        if sport is not None:
            options += ["sport", sport]

        if dport is not None:
            options += ["dport", dport]

        cmd += " ".join(options)
        out = self.check_output(cmd)
        return json.loads(out)

    def tunnels(self, ifname=None):
        """Returns all configured tunnels

            Optionally, tunnels returned can be filtered with the interface name.
            This can be faster in busy tunnel installations.

            Selectors:
            - ifname

        """
        cmd = f"{self._ip} --json tunnel show "

        options = []
        if ifname is not None:
            options += [ifname]

        cmd += " ".join(options)
        out = self.check_output(cmd)
        return json.loads(out)

    def vrfs(self):
        """Returns all configured vrfs"""
        cmd = f"{self._ip} --json vrf show"
        out = self.check_output(cmd)
        return json.loads(out)

    def netns(self):
        """Returns all configured network namespaces"""
        cmd = f"{self._ip} --json netns show"
        out = self.check_output(cmd)
        if not out:  # ip netns returns null instead of [] in json mode
            return json.loads("[]\n")
        return json.loads(out)

    def bridge_vlan(self):
        """Returns all configured vlans"""
        cmd = f"{self._bridge} -json vlan show"
        out = self.check_output(cmd)
        return json.loads(out)

    def bridge_fdb(self):
        """Returns all configured fdb entries"""
        cmd = f"{self._bridge} -json fdb show"
        out = self.check_output(cmd)
        return json.loads(out)

    def bridge_mdb(self):
        """Returns all configured mdb entries"""
        cmd = f"{self._bridge} -json mdb show"
        out = self.check_output(cmd)
        return json.loads(out)

    def bridge_link(self):
        """Returns all configured links"""
        cmd = f"{self._bridge} -json link show"
        out = self.check_output(cmd)
        return json.loads(out)
