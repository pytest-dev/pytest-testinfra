# -*- coding: utf8 -*-
# Copyright © 2015 Philippe Pepiot
#
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
from __future__ import absolute_import

from testinfra.backend import base

import os

try:
    from docker import Client
except ImportError:
    HAS_DOCKER = False
else:
    HAS_DOCKER = True


class DockerBackend(base.BaseBackend):
    _backend_type = "docker"

    def __init__(self, host, *args, **kwargs):
        if not HAS_DOCKER:
            raise RuntimeError((
                "You must install docker-py package (pip install docker-py) "
                "to use the docker-py backend"))
        self.docker_host = os.getenv("DOCKER_HOST", "/var/run/docker.sock")
        self.image = host
        self.cli = Client(base_url=self.docker_host)

        super(DockerBackend, self).__init__(*args, **kwargs)

    def run(self, command, *args, **kwargs):
        container = self.cli.create_container(self.image,
                                              "tail -f /dev/null")
        self.cli.start(container)
        inspect = self.cli.inspect_container(container)
        if not inspect['State']['Running']:
            raise RuntimeError("Docker Container Start Failed")

        execution = self.cli.exec_create(container,
                                         self.quote(command, *args),)
        out = self.cli.exec_start(execution)
        inspection = self.cli.exec_inspect(execution)
        self.cli.remove_container(container, v=True, force=True, )
        return base.CommandResult(self,
                                  inspection["ExitCode"], out, "", command)
