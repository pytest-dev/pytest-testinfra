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


class Incus(Module):
    """Test incus instances running on system.

    Example:

    >>> nginx = host.incus("app_nginx")
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
        output = self.check_output("incus list --format json name=%s", self._name)
        return json.loads(output)[0]

    @property
    def is_running(self):
        return self.inspect()["status"] == "Running"

    @property
    def name(self):
        return self.inspect()["name"]

    @classmethod
    def get_instances(cls, **filters):
        """Return a list of instances

        By default, return a list of all instances, including non-running
        instances.

        Filtering can be done using filters keys defined in
        incus-list(1).

        Multiple filters for a given key are handled by giving a list of
        strings as value.

        >>> host.incus.get_instances()
        [<incus nginx>, <incus redis>, <incus app>]
        # Get all running instances
        >>> host.incus.get_instances(status="running")
        [<incus app>]
        # Get instances named "nginx"
        >>> host.incus.get_instances(name="nginx")
        [<incus nginx>]
        # Get instances named "nginx" or "redis"
        >>> host.incus.get_instances(name=["nginx", "redis"])
        [<incus nginx>, <incus redis>]
        """
        cmd = "incus list --format csv --columns n"
        args = []

        for key, value in filters.items():
            if isinstance(value, (list, tuple)):
                value = ",".join(value)

            cmd += " %s=%s"
            args += [key, value]

        result = []

        for instance_name in cls(None).check_output(cmd, *args).splitlines():
            result.append(cls(instance_name))

        return result

    def __repr__(self):
        return f"<incus {self._name}>"
