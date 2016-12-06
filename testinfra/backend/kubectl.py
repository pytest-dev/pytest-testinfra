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

from __future__ import unicode_literals
from __future__ import absolute_import

from testinfra.backend import base


class KubectlBackend(base.BaseBackend):
    NAME = "kubectl"

    def __init__(self, name, *args, **kwargs):
        self.name, self.user = self.parse_containerspec(name)
        if "/" in self.name:
            self.name, self.container = self.name.split("/", 1)
        else:
            self.container = None
        super(KubectlBackend, self).__init__(self.name, *args, **kwargs)

    def run(self, command, *args, **kwargs):
        cmd = self.get_command(command, *args)
        # `kubectl exec` does not support specifying the user to run as.
        # See https://github.com/kubernetes/kubernetes/issues/30656
        if self.container is None:
            out = self.run_local(
                "kubectl exec %s -- /bin/sh -c %s", self.name, cmd)
        else:
            out = self.run_local(
                "kubectl exec %s -c %s -- /bin/sh -c %s",
                self.name, self.container, cmd)
        out.command = self.encode(cmd)
        return out
