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

try:
    import salt.runner
    import salt.config
except ImportError:
    raise RuntimeError(
        "You must install salt package to use the salt runner backend")

from testinfra.backend import base


class SaltRunnerBackend(base.BaseBackend):
    HAS_RUN_SALT = True
    NAME = "salt_run"

    def __init__(self, host, *args, **kwargs):
        self.host = host
        self.config = "/etc/salt/master"
        self._runner = None
        super(SaltRunnerBackend, self).__init__(self.host, *args, **kwargs)

    @property
    def runner(self):
        if self._runner is None:
            self._runner = salt.runner.RunnerClient(salt.config.client_config(self.config))
        return self._runner

    def run(self, command, *args, **kwargs):
        command = self.get_command(command, *args)
        out = self.salt_runner(command[0], command[1:])
        return self.result(out['retcode'], command, out['stdout'],
                           out['stderr'])

    def salt_runner(self, func, *args):
        out = {}
        try:
            out["stdout"] = self.runner.cmd(func, arg=args or [])
            out["retcode"] = 0
        except KeyError:
            out["stderr"] = "Unknown function, check salt-run -d for complete list"
            out['retcode'] = 1
        except ValueError:
            out["stderr"] = "No result found"
            out['retcode'] = 2
        return out
