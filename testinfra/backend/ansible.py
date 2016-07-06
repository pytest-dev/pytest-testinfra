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

import logging
import pprint

from testinfra.backend import base

logger = logging.getLogger("testinfra")


class AnsibleBackend(base.BaseBackend):
    NAME = "ansible"
    HAS_RUN_ANSIBLE = True

    def __init__(self, host, ansible_inventory=None, *args, **kwargs):
        self.host = host
        self.ansible_inventory = ansible_inventory
        self._ansible_runner = None
        super(AnsibleBackend, self).__init__(host, *args, **kwargs)

    @property
    def ansible_runner(self):
        if self._ansible_runner is None:
            from testinfra.utils.ansible_runner import AnsibleRunner
            self._ansible_runner = AnsibleRunner(self.ansible_inventory)
        return self._ansible_runner

    def run(self, command, *args):
        command = self.get_command(command, *args)
        out = self.run_ansible("shell", module_args=command)

        # Ansible return an unicode object but this is bytes ...
        # A simple test case is:
        # >>> assert File("/bin/true").content == open("/bin/true").read()
        stdout_bytes = b"".join((chr(ord(c)) for c in out['stdout']))
        stderr_bytes = b"".join((chr(ord(c)) for c in out['stderr']))

        result = base.CommandResult(
            self, out['rc'],
            stdout_bytes,
            stderr_bytes,
            command,
            stdout=out["stdout"], stderr=out["stderr"],
        )
        logger.info("RUN %s", result)
        return result

    def run_ansible(self, module_name, module_args=None, **kwargs):
        result = self.ansible_runner.run(
            self.host, module_name, module_args,
            **kwargs)
        logger.info(
            "RUN Ansible(%s, %s, %s): %s",
            repr(module_name), repr(module_args), repr(kwargs),
            pprint.pformat(result))
        return result

    def get_variables(self):
        return self.ansible_runner.get_variables(self.host)

    @classmethod
    def get_hosts(cls, host, **kwargs):
        from testinfra.utils.ansible_runner import AnsibleRunner
        return AnsibleRunner(kwargs.get("ansible_inventory")).get_hosts(host)
