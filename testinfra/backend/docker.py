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

from testinfra.backend import base


class DockerBackend(base.BaseBackend):
    NAME = "docker"

    def __init__(self, name, *args, **kwargs):
        self.name, self.user = self.parse_containerspec(name)
        super().__init__(self.name, *args, **kwargs)

    def run(self, command, *args, **kwargs):
        cmd = self.get_command(command, *args)
        if self.user is not None:
            out = self.run_local(
                "docker exec -u %s %s /bin/sh -c %s", self.user, self.name, cmd
            )
        else:
            out = self.run_local("docker exec %s /bin/sh -c %s", self.name, cmd)
        out.command = self.encode(cmd)
        return out
