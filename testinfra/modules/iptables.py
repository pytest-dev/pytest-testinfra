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

from testinfra.modules.base import InstanceModule


class Iptables(InstanceModule):
    """Test iptables rule exists"""

    def __init__(self):
        super().__init__()
        # support for -w argument (since 1.6.0)
        # https://git.netfilter.org/iptables/commit/?id=aaa4ace72b
        # centos 6 has no support
        # centos 7 has 1.4 patched
        self._has_w_argument = None

    def _iptables_command(self, version):
        if version == 4:
            iptables = "iptables"
        elif version == 6:
            iptables = "ip6tables"
        else:
            raise RuntimeError("Invalid version: {}".format(version))
        if self._has_w_argument is False:
            return iptables
        else:
            return "{} -w 90".format(iptables)

    def _run_iptables(self, version, cmd, *args):
        ipt_cmd = "{} {}".format(self._iptables_command(version), cmd)
        if self._has_w_argument is None:
            result = self.run_expect([0, 2], ipt_cmd, *args)
            if result.rc == 2:
                self._has_w_argument = False
                return self._run_iptables(version, cmd, *args)
            else:
                self._has_w_argument = True
                return result.stdout.rstrip("\r\n")
        else:
            return self.check_output(ipt_cmd, *args)

    def rules(self, table="filter", chain=None, version=4):
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
        cmd, args = "-t %s -S", [table]
        if chain:
            cmd += " %s"
            args += [chain]

        rules = []
        for line in self._run_iptables(version, cmd, *args).splitlines():
            line = line.replace("\t", " ")
            rules.append(line)
        return rules
