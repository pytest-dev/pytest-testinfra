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
from testinfra.utils.ansible_runner import AnsibleRunner
from testinfra.utils.ansible_runner import to_bytes

logger = logging.getLogger("testinfra")


class AnsibleBackend(base.BaseBackend):
    NAME = "ansible"
    HAS_RUN_ANSIBLE = True

    def __init__(self, host, ansible_inventory=None, *args, **kwargs):
        self.host = host
        self.ansible_inventory = ansible_inventory
        super(AnsibleBackend, self).__init__(host, *args, **kwargs)

    @property
    def ansible_runner(self):
        return AnsibleRunner.get_runner(self.ansible_inventory)

    def run(self, command, *args, **kwargs):
        command = self.get_command(command, *args)
        out = self.run_ansible("shell", module_args=command)
        return self.result(
            out['rc'],
            command,
            stdout_bytes=None,
            stderr_bytes=None,
            stdout=out["stdout"], stderr=out["stderr"],
        )

    def encode(self, data):
        return to_bytes(data)

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
        inventory = kwargs.get('ansible_inventory')
        return AnsibleRunner.get_runner(inventory).get_hosts(host)
