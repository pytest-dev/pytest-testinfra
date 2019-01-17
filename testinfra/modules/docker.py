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

import json


class Docker(Module):

    """Test docker containers running on system.

    Example:

    >>> host = testinfra.get_host('local://')

    >>> nginx = host.docker("hardcore_benz")
    >>> assert nginx.is_running
    >>> print(nginx.id)
    >>> print(nginx.name)
    >>> print(nginx.image_id)

    >>> nginx2 = host.docker("6820b6f1121c")
    >>> nginx2.is_running
    """

    def __init__(self, inst_name):
        self.inst_name = inst_name
        super(Docker, self).__init__()

    @property
    def is_running(self):
        cmd = self.run("docker ps --format '{{ .ID }} {{ .Names }}'")

        if cmd.stdout == "":
            return False

        for entry in cmd.stdout.splitlines():
            c_id, c_name = entry.split()
            if c_id == self.inst_name or c_name == self.inst_name:
                return True

        return False

    def inspect(self):
        cmd = self.run("docker inspect %s", self.inst_name)
        json_out = json.loads(cmd.stdout)

        if len(json_out) == 1:
            return json_out[0]

    @property
    def id(self):
        return self.inspect()["Id"][:12]  # display only first twelve chars

    @property
    def name(self):
        return self.inspect()["Name"][1:]  # get rid of slash in front

    @property
    def image_id(self):
        # display only first twelve chars
        return self.inspect()["Image"].split(':')[1][:12]

    def __repr__(self):
        return "<docker %s>" % (self.inst_name)
