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


class Group(Module):
    """Test unix group"""

    def __init__(self, name=None):
        self.name = name
        super(Group, self).__init__()

    @property
    def exists(self):
        return self.run_expect([0, 2], "getent group %s", self.name).rc == 0

    @property
    def gid(self):
        return int(self.check_output(
            "getent group %s | cut -d':' -f3", self.name))

    def __repr__(self):
        return "<group %s>" % (self.name,)
