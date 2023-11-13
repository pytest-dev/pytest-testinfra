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
    raise RuntimeError("You must install salt package to use the salt backend")

from typing import Any, Optional

from testinfra.backend import base


class SaltBackend(base.BaseBackend):
    HAS_RUN_SALT = True
    NAME = "salt"

    def __init__(self, host: str, *args: Any, **kwargs: Any):
        self.host = host
        self._client: Optional[salt.client.LocalClient] = None
        super().__init__(self.host, *args, **kwargs)

    @property
    def client(self) -> salt.client.LocalClient:
        if self._client is None:
            self._client = salt.client.LocalClient()
        return self._client

    def run(self, command: str, *args: str, **kwargs: Any) -> base.CommandResult:
        command = self.get_command(command, *args)
        out = self.run_salt("cmd.run_all", [command])
        return self.result(
            out["retcode"],
            self.encode(command),
            stdout=out["stdout"],
            stderr=out["stderr"],
        )

    def run_salt(self, func: str, args: Any = None) -> Any:
        out = self.client.cmd(self.host, func, args or [])
        if self.host not in out:
            raise RuntimeError(
                "Error while running {}({}): {}. "
                "Minion not connected ?".format(func, args, out)
            )
        return out[self.host]

    @classmethod
    def get_hosts(cls, host: str, **kwargs: Any) -> list[str]:
        if host is None:
            host = "*"
        if any(c in host for c in "@*[?"):
            client = salt.client.LocalClient()
            if "@" in host:
                hosts = client.cmd(host, "test.true", tgt_type="compound").keys()
            else:
                hosts = client.cmd(host, "test.true").keys()
            if not hosts:
                raise RuntimeError("No host matching '{}'".format(host))
            return sorted(hosts)
        return super().get_hosts(host, **kwargs)
