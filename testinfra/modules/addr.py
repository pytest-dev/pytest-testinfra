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
    """Test connections"""

    def __init__(self, address, port, protocol):
        self.address = address
        self.port = port
        self.protocol = protocol
        super(Addr, self).__init__()

    def is_reachable(self):
        result = "command to run"

        if self.protocol == "tcp":
            result = self.run_test("echo | nc -vw 1 %s %s", self.address, self.port)
        elif self.protocol == "udp":
            result = self.run_test("echo | nc -uvw 1 %s %s", self.address, self.port)
        else:
            pass # do something for icmp

        if result.rc != 0:
            return False

        out = result.stdout.strip()

        return True