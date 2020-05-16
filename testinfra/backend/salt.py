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

try:
    import salt.client
except ImportError:
    raise RuntimeError(
        "You must install salt package to use the salt backend")

from testinfra.backend import base


class SaltBackend(base.BaseBackend):
    HAS_RUN_SALT = True
    NAME = "salt"

    def __init__(self, host, *args, **kwargs):
        self.host = host
        self._client = None
        super().__init__(self.host, *args, **kwargs)

    @property
    def client(self):
        if self._client is None:
            self._client = salt.client.LocalClient()
        return self._client

    def run(self, command, *args, **kwargs):
        command = self.get_command(command, *args)
        out = self.run_salt("cmd.run_all", [command])
        return self.result(out['retcode'], command, out['stdout'],
                           out['stderr'])

    def run_salt(self, func, args=None):
        out = self.client.cmd(self.host, func, args or [])
        if self.host not in out:
            raise RuntimeError(
                "Error while running %s(%s): %s. Minion not connected ?" % (
                    func, args, out))
        return out[self.host]

    @classmethod
    def get_hosts(cls, host, **kwargs):
        if host is None:
            host = "*"
        if any([c in host for c in "@*[?"]):
            client = salt.client.LocalClient()
            if "@" in host:
                hosts = client.cmd(
                    host, "test.true", expr_form="compound").keys()
            else:
                hosts = client.cmd(host, "test.true").keys()
            if not hosts:
                raise RuntimeError("No host matching '%s'" % (host,))
            return sorted(hosts)
        return super().get_hosts(host, **kwargs)
