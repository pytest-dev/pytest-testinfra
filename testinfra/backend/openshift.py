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

from testinfra.backend import base


class OpenShiftBackend(base.BaseBackend):
    NAME = "openshift"

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.container = kwargs.get('container')
        self.namespace = kwargs.get('namespace')
        self.kubeconfig = kwargs.get('kubeconfig')
        super().__init__(self.name, *args, **kwargs)

    def run(self, command, *args, **kwargs):
        cmd = self.get_command(command, *args)
        # `oc exec` does not support specifying the user to run as.
        # See https://github.com/kubernetes/kubernetes/issues/30656
        oscmd = 'oc '
        oscmd_args = []
        if self.kubeconfig is not None:
            oscmd += '--kubeconfig="%s" '
            oscmd_args.append(self.kubeconfig)
        if self.namespace is not None:
            oscmd += '-n %s '
            oscmd_args.append(self.namespace)
        if self.container is not None:
            oscmd += '-c %s '
            oscmd_args.append(self.container)
        oscmd += 'exec %s -- /bin/sh -c %s'
        oscmd_args.extend([self.name, cmd])
        out = self.run_local(oscmd, *oscmd_args)
        return out
