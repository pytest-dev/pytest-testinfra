# -*- coding: utf8 -*-
# Copyright © 2016 Philippe Pepiot
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

from __future__ import print_function

import testinfra

template = """
Host %s
  HostName %s
  User root
  Port 22
  UserKnownHostsFile /dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  IdentityFile .cache/insecure_private_key
  IdentitiesOnly yes
  LogLevel FATAL
"""


class DockerComposeService(object):
    _services = None

    @classmethod
    def get_services(cls):
        if cls._services is not None:
            return cls._services

        cls._services = {}
        Command = testinfra.get_backend("local://").get_module("Command")

        for line in Command.check_output((
            "docker-compose ps -q | xargs docker inspect --format "
            """'{{ index .Config.Labels "com.docker.compose.service" }} """
            """{{ .Name }} """
            """{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'"""
        )).splitlines():
            service, name, ip = line.split()
            cls._services[service] = {
                "name": name[1:] if name[0] == "/" else name,
                "ip": ip,
            }

        return cls._services

    @classmethod
    def get(cls, service):
        return cls.get_services()[service]


def docker_compose_to_ssh_config():
    for service, values in DockerComposeService.get_services().items():
        print(template % (service, values["ip"]))


if __name__ == "__main__":
    docker_compose_to_ssh_config()
