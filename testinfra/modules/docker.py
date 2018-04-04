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
import json

from testinfra.modules.base import Module


class Docker(Module):

    """Test docker containers running on system.

    Example:

    >>> nginx = host.docker("app_nginx")
    >>> nginx.is_running
    True
    >>> nginx.id
    '7e67dc7495ca8f451d346b775890bdc0fb561ecdc97b68fb59ff2f77b509a8fe'
    >>> nginx.name
    'app_nginx'
    """

    def __init__(self, name):
        self._name = name
        super(Docker, self).__init__()

    def inspect(self):
        output = self.check_output("docker inspect %s", self._name)
        return json.loads(output)[0]

    @property
    def is_running(self):
        return self.inspect()['State']['Running']

    @property
    def id(self):
        return self.inspect()["Id"]

    @property
    def name(self):
        return self.inspect()["Name"][1:]  # get rid of slash in front

    def __repr__(self):
        return "<docker %s>" % (self._name)
