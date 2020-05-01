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


class Environment(InstanceModule):
    """Get Environment variables

    Example:

     >>> host.environment()
    {
        "EDITOR": "vim",
        "SHELL": "/bin/bash",
        [...]
    }
    """

    def __call__(self):
        ret_val = dict(
            i.split('=', 1) for i in self.check_output('env -0').split(
                '\x00') if i
        )
        return ret_val

    def __repr__(self):
        return "<environment>"
