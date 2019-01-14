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
from testinfra.modules.base import Module


class Docker(Module):
    """Test docker containers running on system.

    Example:

    >>> host = testinfra.get_host('local://')

    >>> nginx = host.docker("nginx:latest")
    >>> assert nginx.is_running
    """

    def __init__(self, name):
        self.name = name
        super(Docker, self).__init__()

    @property
    def is_running(self):
        cmd = self.run("docker ps -q -f ancestor=%s --format '{{.Image}}'",
                       self.name)

        if cmd.stdout == "":
            return False

        images = cmd.stdout.splitlines()

        if all(i == self.name for i in images):
            return True

        return False

    def __repr__(self):
        return "<docker %s>" % (self.name)
