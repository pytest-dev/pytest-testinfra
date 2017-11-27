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

    def rules(self, table='filter', chain=None):
        """Returns list of iptables rules

           Based on ouput of `iptables -t TABLE -S CHAIN` command

             optionally takes takes the following arguments:
               - table: defaults to `filter`
               - chain: defaults to all chains

        >>> host.iptables.rules()
        [
            '-P INPUT ACCEPT',
            '-P FORWARD ACCEPT',
            '-P OUTPUT ACCEPT',
            '-A INPUT -i lo -j ACCEPT',
            '-A INPUT -j REJECT'
            '-A FORWARD -j REJECT'
        ]
        >>> host.iptables().get_rules("nat", "INPUT")
        ['-P PREROUTING ACCEPT']

        """

        rules = []
        if chain:
            cmd = "iptables -t {0} -S {1}".format(table, chain)
        else:
            cmd = "iptables -t {0} -S".format(table)

        for line in self.check_output(cmd).splitlines():
            line = line.replace("\t", " ")
            rules.append(line)
        return rules
