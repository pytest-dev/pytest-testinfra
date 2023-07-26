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

import logging
import pprint
from typing import Any, Optional

from testinfra.backend import base
from testinfra.utils.ansible_runner import AnsibleRunner

logger = logging.getLogger("testinfra")


class AnsibleBackend(base.BaseBackend):
    NAME = "ansible"
    HAS_RUN_ANSIBLE = True

    def __init__(
        self,
        host: str,
        ansible_inventory: Optional[str] = None,
        ssh_config: Optional[str] = None,
        ssh_identity_file: Optional[str] = None,
        force_ansible: bool = False,
        *args: Any,
        **kwargs: Any,
    ):
        self.host = host
        self.ansible_inventory = ansible_inventory
        self.ssh_config = ssh_config
        self.ssh_identity_file = ssh_identity_file
        self.force_ansible = force_ansible
        super().__init__(host, *args, **kwargs)

    @property
    def ansible_runner(self) -> AnsibleRunner:
        return AnsibleRunner.get_runner(self.ansible_inventory)

    def run(self, command: str, *args: str, **kwargs: Any) -> base.CommandResult:
        command = self.get_command(command, *args)
        if not self.force_ansible:
            host = self.ansible_runner.get_host(
                self.host,
                ssh_config=self.ssh_config,
                ssh_identity_file=self.ssh_identity_file,
            )
            if host is not None:
                return host.run(command)
        out = self.run_ansible("shell", module_args=command, check=False)
        return self.result(
            out["rc"],
            self.encode(command),
            out["stdout"],
            out["stderr"],
        )

    def run_ansible(
        self, module_name: str, module_args: Optional[str] = None, **kwargs: Any
    ) -> Any:
        def get_encoding() -> str:
            return self.encoding

        result = self.ansible_runner.run_module(
            self.host, module_name, module_args, get_encoding=get_encoding, **kwargs
        )
        logger.info(
            "RUN Ansible(%s, %s, %s): %s",
            repr(module_name),
            repr(module_args),
            repr(kwargs),
            pprint.pformat(result),
        )
        return result

    def get_variables(self) -> dict[str, Any]:
        return self.ansible_runner.get_variables(self.host)

    @classmethod
    def get_hosts(cls, host: str, **kwargs: Any) -> list[str]:
        inventory = kwargs.get("ansible_inventory")
        return AnsibleRunner.get_runner(inventory).get_hosts(host or "all")
