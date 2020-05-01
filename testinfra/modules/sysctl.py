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
from testinfra.utils import cached_property


class Sysctl(InstanceModule):
    """Test kernel parameters

    >>> host.sysctl("kernel.osrelease")
    "3.16.0-4-amd64"
    >>> host.sysctl("vm.dirty_ratio")
    20
    """
    @cached_property
    def _sysctl_command(self):
        return self.find_command('sysctl')

    def __call__(self, name):
        value = self.check_output("%s -n %s", self._sysctl_command, name)
        try:
            return int(value)
        except ValueError:
            return value

    def __repr__(self):
        return "<sysctl>"
