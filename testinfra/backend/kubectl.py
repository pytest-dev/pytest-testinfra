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
        self.name = name
        self.container = kwargs.get('container')
        self.namespace = kwargs.get('namespace')
        super(KubectlBackend, self).__init__(self.name, *args, **kwargs)

    def run(self, command, *args, **kwargs):
        cmd = self.get_command(command, *args)
        # `kubectl exec` does not support specifying the user to run as.
        # See https://github.com/kubernetes/kubernetes/issues/30656
        kcmd = 'kubectl '
        kcmd_args = []
        if self.namespace is not None:
            kcmd += '-n %s '
            kcmd_args.append(self.namespace)
        if self.container is not None:
            kcmd += '-c %s '
            kcmd_args.append(self.container)
        kcmd += 'exec %s -- /bin/sh -c %s'
        kcmd_args.extend([self.name, cmd])
        out = self.run_local(kcmd, *kcmd_args)
        return out
