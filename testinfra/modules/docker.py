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

    >>> nginx = host.docker("nginx")
    >>> assert nginx.is_running

    >>> assert nginx.is_listening('8000', '8001')

    >>> assert nginx.version == 'latest'
    """

    def __init__(self, name):
        self.name = name
        super(Docker, self).__init__()

    def running_image(self):
        cmd = self.run("docker ps -q -f ancestor=%s --format '{{.Image}}'",
                       self.name)
        images = cmd.stdout.splitlines()
        assert all(i == self.name for i in images) and cmd.stdout != ""
        return images[0]

    def running_ports(self):
        cmd = self.run("docker ps -q -f ancestor=%s --format '{{.Ports}}'",
                       self.name)
        names = cmd.stdout.strip().split(', ')
        ports = [p.split('->')[0].split(':')[1] for p in names]
        return ports

    @property
    def is_running(self):
        # assert fails if container corresponding to image is not running
        self.running_image()
        return True

    def is_listening(self, ports):
        run_ports = self.running_ports()
        assert all(i in ports for i in run_ports)
        return True

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
