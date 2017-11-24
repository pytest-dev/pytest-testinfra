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


class Iptables(Module):
    """Test iptables rule exists"""

    def __init__(self, rule=None, table=None):
        self.rule = rule
        self.table = table
        super(Iptables, self).__init__()

    @property
    def exists(self):
        """Returns true if iptables rule exists in table

        Defaults to looking in 'filter' table.

        >>> host.iptables_rule("-A INPUT -j REJECT").exists
        True
        >>> host.iptables_rule("-A INPUT -i lo -j REJECT").exists
        False
        >>> host.iptables_rule(
            "-A PREROUTING -d 192.168.0.1/32 -j REDIRECT",
            "nat"
        ).exists
        True

        """

        rules = self.get_rules()
        return self.rule in rules

    def get_rules(self, table='filter', chain=None):
        """Returns list of iptables rules by running

           Based on ouput of 'iptables -S' command

             optionally takes takes the following arguments:
               - table: defaults to 'filter'
               - chain: defaults to all chains

        >>> host.iptables().get_rules()
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
        cmd = "iptables"

        if self.table:
            cmd += " -t %s" % (self.table)
        else:
            cmd += " -t %s" % (table)

        cmd += " -S"

        if chain:
            cmd += " %s" % (chain)

        for line in self.check_output(cmd).splitlines():
            line = line.replace("\t", " ")
            rules.append(line)
        return rules
