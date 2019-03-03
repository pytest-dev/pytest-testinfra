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

from testinfra.modules.base import InstanceModule


class Iptables(InstanceModule):
    """Test iptables rule exists"""

    def rules(self, table='filter', chain=None, version=4):
        """Returns list of iptables rules

           Based on ouput of `iptables -t TABLE -S CHAIN` command

             optionally takes takes the following arguments:
               - table: defaults to `filter`
               - chain: defaults to all chains
               - version: default 4 (iptables), optionally 6 (ip6tables)

        >>> host.iptables.rules()
        [
            '-P INPUT ACCEPT',
            '-P FORWARD ACCEPT',
            '-P OUTPUT ACCEPT',
            '-A INPUT -i lo -j ACCEPT',
            '-A INPUT -j REJECT'
            '-A FORWARD -j REJECT'
        ]
        >>> host.iptables.rules("nat", "INPUT")
        ['-P PREROUTING ACCEPT']

        """

        if version == 4:
            iptables = "iptables"
        elif version == 6:
            iptables = "ip6tables"
        else:
            raise RuntimeError("Invalid version: %s" % version)

        rules = []
        if chain:
            cmd = "{0} -t {1} -S {2}".format(iptables, table, chain)
        else:
            cmd = "{0} -t {1} -S".format(iptables, table)

        for line in self.check_output(cmd).splitlines():
            line = line.replace("\t", " ")
            rules.append(line)
        return rules
