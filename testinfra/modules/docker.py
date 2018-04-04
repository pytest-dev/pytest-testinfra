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
    """
    Test docker containers running on system.
 
    Example:

    >>> host = testinfra.get_host('local://')

    >>> nginx = host.docker("nginx")
    >>> assert nginx.is_running

    >>> nginx.is_listening = ['8080', '8081']
    >>> assert nginx.is_listening

    >>> assert nginx.version == 'latest'
    """

    def __init__(self, name):
        self.name = name
        super(Docker, self).__init__()

    def running_image(self):
        cmd = self.run("docker ps -q -f ancestor=%s --format '{{.Image}}'", self.name)
        images = cmd.stdout.splitlines()
        assert all(map(lambda i : i == self.name, images)) and cmd.stdout != ""
        return images[0]

    def running_ports(self):
        cmd = self.run("docker ps -q -f ancestor=%s --format '{{.Ports}}'", self.name)
        names = cmd.stdout.splitlines()
        return names

    @property
    def is_running(self):
        image = self.running_image()
        return True

    @property
    def is_listening(self):
        ports = self.running_ports()
        ports = map(lambda p : p.split('->')[0].split(':')[1], ports)
        assert all(map(lambda i : i in self._ports, ports))
        return True

    @is_listening.setter
    def is_listening(self, ports):
        self._ports = ports
        
    def versions(self):
        image = self.running_image()
        cmd = self.run("docker images %s --format '{{.Tag}}'", image)
        return cmd.stdout.splitlines()

    @property
    def version(self):
        version = self.versions()
        assert len(version) == 1
        return version[0]


    def __repr__(self):
        return "<docker>"
