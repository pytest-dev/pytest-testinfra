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

from testinfra.modules.base import Module


class IProute2(Module):
    """Tests network configuration via iproute2 commands

    Currently supported:

    * ip-address
    * ip-link
    * ip-route
    * ip-rule
    * ip-vrf
    * ip-tunnel
    * ip-netns
    * bridge vlan
    * bridge link
    * bridge fdb
    * bridge mdb

    Optional module-level arguments can also be provided to control execution:

        * **family**: force iproute2 tools to use a specific protocol family

        >>> host.iproute2(family="inet").addresses()

        * **namespace**: execute iproute2 tools inside the provided namespace

        >>> host.iproute2(namespace="test").addresses()

    """

    def __init__(self, family=None, namespace=None):
        self.family = family
        self.namespace = namespace
        super().__init__()

    def __repr__(self):
        return "<ip>"

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            return LinuxIProute2
        raise NotImplementedError

    @property
    def exists(self):
        """Returns True if ip -V succeeds

        >>> host.iproute2.exists
        True

        """

    @property
    def bridge_exists(self):
        """Returns True if bridge -V succeeds

        >>> host.iproute2.bridge_exists
        True

        """

    def addresses(self, address=None, ifname=None, local=None):
        """Returns the addresses associated with interfaces

        >>> host.iproute2.addresses()
        [{'ifindex': 1,
          'ifname': 'lo',
          'flags': ['LOOPBACK', 'UP', 'LOWER_UP'],
          'mtu': 65536,
          'qdisc': 'noqueue',
          'operstate': 'UNKNOWN',
          'group': 'default',
          'txqlen': 1000,
          'link_type': 'loopback',
          'address': '00:00:00:00:00:00',
          'broadcast': '00:00:00:00:00:00',
          'addr_info': [{'family': 'inet',
            'local': '127.0.0.1',
            'prefixlen': 8,
            'scope': 'host',
            'label': 'lo',
            'valid_life_time': 4294967295,
            'preferred_life_time': 4294967295},
           {'family': 'inet6',
            'local': '::1',
            'prefixlen': 128,
            'scope': 'host',
            'noprefixroute': True,
            'valid_life_time': 4294967295,
            'preferred_life_time': 4294967295}]}]

        Optionally, results can be filtered with the following selectors:

        * address
        * ifname
        * local

        """

    def links(self):
        """Returns links and their state.

        >>> host.iproute2.links()
        [{'ifindex': 1,
            'ifname': 'lo',
            'flags': ['LOOPBACK', 'UP', 'LOWER_UP'],
            'mtu': 65536,
            'qdisc': 'noqueue',
            'operstate': 'UNKNOWN',
            'linkmode': 'DEFAULT',
            'group': 'default',
            'txqlen': 1000,
            'link_type': 'loopback',
            'address': '00:00:00:00:00:00',
            'broadcast': '00:00:00:00:00:00'}]

        """

    def routes(
        self, table="all", device=None, scope=None, proto=None, src=None, metric=None
    ):
        """Returns the routes installed in *all* routing tables.

        >>> host.iproute2.routes()
        [{'dst': '169.254.0.0/16',
          'dev': 'wlp4s0',
          'scope': 'link',
          'metric': 1000,
          'flags': []},
         {'type': 'multicast',
          'dst': 'ff00::/8',
          'dev': 'wlp4s0',
          'table': 'local',
          'protocol': 'kernel',
          'metric': 256,
          'flags': [],
          'pref': 'medium'}]

        Optionally, routes returned can be filtered with the following
        selectors. This can be useful in busy routing tables.

        * table
        * device (maps to ip-route's 'dev' selector)
        * scope
        * proto
        * src
        * metric

        """

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
        """Returns the rules our routing policy consists of.

        >>> host.iproute2.rules()
        [{'priority': 0, 'src': 'all', 'table': 'local'},
         {'priority': 32765, 'src': '1.2.3.4', 'table': '123'},
         {'priority': 32766, 'src': 'all', 'table': 'main'},
         {'priority': 32767, 'src': 'all', 'table': 'default'}]

        Optionally, rules returned can be filtered with the following
        selectors. This can be useful in busy rulesets.

        * src (maps to ip-rule's 'from' selector)
        * to
        * tos
        * fwmark
        * iif
        * oif
        * pref
        * uidrange
        * ipproto
        * sport
        * dport

        """

    def tunnels(self, ifname=None):
        """Returns all configured tunnels

        >>> host.iproute2.tunnels()
        [{'ifname': 'test1',
          'mode': 'ip/ip',
          'remote': '127.0.0.2',
          'local': '0.0.0.0'}]

        Optionally, tunnels returned can be filtered with the interface name.
        This can be faster in busy tunnel installations.

        * ifname

        """

    def vrfs(self):
        """Returns all configured vrfs"""
        cmd = f"{self._ip} --json vrf show"
        out = self.check_output(cmd)
        return json.loads(out)

    def netns(self):
        """Returns all configured network namespaces

        >>> host.iproute2.netns()
        [{'name': 'test'}]
        """

    def bridge_vlan(self):
        """Returns all configured vlans

        >>> host.iproute2.bridge_vlan()
        []
        """

    def bridge_fdb(self):
        """Returns all configured fdb entries

        >>> host.iproute2.bridge_fdb()
        [{'mac': '33:33:00:00:00:01',
          'ifname': 'enp0s31f6',
          'flags': ['self'],
          'state': 'permanent'}]
        """

    def bridge_mdb(self):
        """Returns all configured mdb entries

        >>> host.iproute2.bridge_mdb()
        [{'mdb': [], 'router': {}}]

        """

    def bridge_link(self):
        """Returns all configured links

        >>> host.iproute2.bridge_link()
        []
        """


class LinuxIProute2(IProute2):
    @functools.cached_property
    def _ip(self):
        ip_cmd = self.find_command("ip")
        if self.namespace is not None:
            ip_cmd = f"{ip_cmd} -n {self.namespace}"
        if self.family is not None:
            ip_cmd = f"{ip_cmd} -f {self.family}"
        return ip_cmd

    @functools.cached_property
    def _bridge(self):
        bridge_cmd = self.find_command("bridge")
        if self.namespace is not None:
            bridge_cmd = f"{bridge_cmd} -n {self.namespace}"
        return bridge_cmd

    @property
    def exists(self):
        """Returns True if ip -V succeeds

        >>> host.iproute2.exists
        True

        """
        return self.run_test("{} -V".format(self._ip)).rc == 0

    @property
    def bridge_exists(self):
        """Returns True if bridge -V succeeds

        >>> host.iproute2.bridge_exists
        True

        """
        return self.run_test("{} -V".format(self._bridge)).rc == 0

    def addresses(self, address=None, ifname=None, local=None):
        """Returns the addresses associated with interfaces

        >>> host.iproute2.addresses()
        [{'ifindex': 1,
          'ifname': 'lo',
          'flags': ['LOOPBACK', 'UP', 'LOWER_UP'],
          'mtu': 65536,
          'qdisc': 'noqueue',
          'operstate': 'UNKNOWN',
          'group': 'default',
          'txqlen': 1000,
          'link_type': 'loopback',
          'address': '00:00:00:00:00:00',
          'broadcast': '00:00:00:00:00:00',
          'addr_info': [{'family': 'inet',
            'local': '127.0.0.1',
            'prefixlen': 8,
            'scope': 'host',
            'label': 'lo',
            'valid_life_time': 4294967295,
            'preferred_life_time': 4294967295},
           {'family': 'inet6',
            'local': '::1',
            'prefixlen': 128,
            'scope': 'host',
            'noprefixroute': True,
            'valid_life_time': 4294967295,
            'preferred_life_time': 4294967295}]}]

        Optionally, results can be filtered with the following selectors:

        * address
        * ifname
        * local

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
        """Returns links and their state.

        >>> host.iproute2.links()
        [{'ifindex': 1,
            'ifname': 'lo',
            'flags': ['LOOPBACK', 'UP', 'LOWER_UP'],
            'mtu': 65536,
            'qdisc': 'noqueue',
            'operstate': 'UNKNOWN',
            'linkmode': 'DEFAULT',
            'group': 'default',
            'txqlen': 1000,
            'link_type': 'loopback',
            'address': '00:00:00:00:00:00',
            'broadcast': '00:00:00:00:00:00'}]

        """
        cmd = f"{self._ip} --json link show"
        out = self.check_output(cmd)
        return json.loads(out)

    def routes(
        self, table="all", device=None, scope=None, proto=None, src=None, metric=None
    ):
        """Returns the routes installed in *all* routing tables.

        >>> host.iproute2.routes()
        [{'dst': '169.254.0.0/16',
          'dev': 'wlp4s0',
          'scope': 'link',
          'metric': 1000,
          'flags': []},
         {'type': 'multicast',
          'dst': 'ff00::/8',
          'dev': 'wlp4s0',
          'table': 'local',
          'protocol': 'kernel',
          'metric': 256,
          'flags': [],
          'pref': 'medium'}]

        Optionally, routes returned can be filtered with the following
        selectors. This can be useful in busy routing tables.

        * table
        * device (maps to ip-route's 'dev' selector)
        * scope
        * proto
        * src
        * metric

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
        """Returns the rules our routing policy consists of.

        >>> host.iproute2.rules()
        [{'priority': 0, 'src': 'all', 'table': 'local'},
         {'priority': 32765, 'src': '1.2.3.4', 'table': '123'},
         {'priority': 32766, 'src': 'all', 'table': 'main'},
         {'priority': 32767, 'src': 'all', 'table': 'default'}]

        Optionally, rules returned can be filtered with the following
        selectors. This can be useful in busy rulesets.

        * src (maps to ip-rule's 'from' selector)
        * to
        * tos
        * fwmark
        * iif
        * oif
        * pref
        * uidrange
        * ipproto
        * sport
        * dport

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

        >>> host.iproute2.tunnels()
        [{'ifname': 'test1',
          'mode': 'ip/ip',
          'remote': '127.0.0.2',
          'local': '0.0.0.0'}]

        Optionally, tunnels returned can be filtered with the interface name.
        This can be faster in busy tunnel installations.

        * ifname

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
        """Returns all configured network namespaces

        >>> host.iproute2.netns()
        [{'name': 'test'}]
        """

        cmd = f"{self._ip} --json netns show"
        out = self.check_output(cmd)
        if not out:  # ip netns returns null instead of [] in json mode
            return json.loads("[]\n")
        return json.loads(out)

    def bridge_vlan(self):
        """Returns all configured vlans

        >>> host.iproute2.bridge_vlan()
        []
        """

        cmd = f"{self._bridge} -json vlan show"
        out = self.check_output(cmd)
        return json.loads(out)

    def bridge_fdb(self):
        """Returns all configured fdb entries

        >>> host.iproute2.bridge_fdb()
        [{'mac': '33:33:00:00:00:01',
          'ifname': 'enp0s31f6',
          'flags': ['self'],
          'state': 'permanent'}]
        """

        cmd = f"{self._bridge} -json fdb show"
        out = self.check_output(cmd)
        return json.loads(out)

    def bridge_mdb(self):
        """Returns all configured mdb entries

        >>> host.iproute2.bridge_mdb()
        [{'mdb': [], 'router': {}}]

        """

        cmd = f"{self._bridge} -json mdb show"
        out = self.check_output(cmd)
        return json.loads(out)

    def bridge_link(self):
        """Returns all configured links

        >>> host.iproute2.bridge_link()
        []
        """

        cmd = f"{self._bridge} -json link show"
        out = self.check_output(cmd)
        return json.loads(out)
