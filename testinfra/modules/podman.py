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
import json

from testinfra.modules.base import Module


class Podman(Module):

    """Test podman containers running on system.

    Example:

    >>> nginx = host.podman("app_nginx")
    >>> nginx.is_running
    True
    >>> nginx.id
    '7e67dc7495ca8f451d346b775890bdc0fb561ecdc97b68fb59ff2f77b509a8fe'
    >>> nginx.name
    'app_nginx'
    """

    def __init__(self, name):
        self._name = name
        super().__init__()

    def inspect(self):
        output = self.check_output("podman inspect %s", self._name)
        return json.loads(output)[0]

    @property
    def is_running(self):
        return self.inspect()['State']['Running']

    @property
    def id(self):
        return self.inspect()["Id"]

    @property
    def name(self):
        return self.inspect()["Name"]

    @classmethod
    def get_containers(cls, **filters):
        """Return a list of containers

        By default return list of all containers, including non-running
        containers.

        Filtering can be done using filters keys defined in
        podman-ps(1).

        Multiple filters for a given key is handled by giving a list of string
        as value.

        >>> host.podman.get_containers()
        [<podman nginx>, <podman redis>, <podman app>]
        # Get all running containers
        >>> host.podman.get_containers(status="running")
        [<podman app>]
        # Get containers named "nginx"
        >>> host.podman.get_containers(name="nginx")
        [<podman nginx>]
        # Get containers named "nginx" or "redis"
        >>> host.podman.get_containers(name=["nginx", "redis"])
        [<podman nginx>, <podman redis>]
        """
        cmd = "podman ps --all --format '{{.Names}}'"
        args = []
        for key, value in filters.items():
            if isinstance(value, (list, tuple)):
                values = value
            else:
                values = [value]
            for v in values:
                cmd += " --filter %s=%s"
                args += [key, v]
        result = []
        for podman_id in cls(None).check_output(cmd, *args).splitlines():
            result.append(cls(podman_id))
        return result

    def __repr__(self):
        return "<podman %s>" % (self._name)
