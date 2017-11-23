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

    def __init__(self, rule, table=None):
        self.rule = rule
        self.table = table
        super(Iptables, self).__init__()

    @property
    def exists(self):
        """Test if file exists

        >>> host.file("/etc/passwd").exists
        True
        >>> host.file("/nonexistent").exists
        False

        """
        rules = self.get_rules()
        return self.rule in rules

    def get_rules(self):
        rules = []
        cmd = "iptables -S"

        if self.table:
            cmd += " -t %s" % (self.table)

        for line in self.check_output(cmd).splitlines():
            line = line.replace("\t", " ")
            rules.append(line)
        return rules
