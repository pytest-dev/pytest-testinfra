# -*- coding: utf8 -*-
# Copyright © 2015 Philippe Pepiot
#
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

try:
    import ansible.inventory
    import ansible.runner
except ImportError:
    HAS_ANSIBLE = False
else:
    HAS_ANSIBLE = True


class AnsibleBackend(base.BaseBackend):
    NAME = "ansible"
    HAS_RUN_ANSIBLE = True

    def __init__(
        self, host, ansible_inventory=None,
        *args, **kwargs
    ):
        self.host = host
        self.ansible_inventory = ansible_inventory
        super(AnsibleBackend, self).__init__(host, *args, **kwargs)

    @staticmethod
    def _check_ansible():
        if not HAS_ANSIBLE:
            raise RuntimeError(
                "You must install ansible package to use the ansible backend")

    def run(self, command, *args):
        self._check_ansible()
        command = self.get_command(command, *args)
        kwargs = {}
        if self.ansible_inventory is not None:
            kwargs["host_list"] = self.ansible_inventory
        out = ansible.runner.Runner(
            pattern=self.host,
            module_name="shell",
            module_args=command,
            **kwargs
        ).run()["contacted"][self.host]

        # Ansible return an unicode object but this is bytes ...
        # A simple test case is:
        # >>> assert File("/bin/true").content == open("/bin/true").read()
        stdout_bytes = b"".join(map(chr, map(ord, out['stdout'])))
        stderr_bytes = b"".join(map(chr, map(ord, out['stderr'])))

        return base.CommandResult(
            self, out['rc'],
            stdout_bytes,
            stderr_bytes,
            command,
            stdout=out["stdout"], stderr=out["stderr"],
        )

    def run_ansible(self, module_name, module_args=None, **kwargs):
        kwargs = kwargs.copy()
        if module_args is not None:
            kwargs["module_args"] = module_args
        if self.ansible_inventory is not None:
            kwargs["host_list"] = self.ansible_inventory
        return ansible.runner.Runner(
            pattern=self.host,
            module_name=module_name,
            **kwargs).run()["contacted"][self.host]

    @classmethod
    def get_hosts(cls, host, **kwargs):
        AnsibleBackend._check_ansible()
        ansible_inventory = kwargs.get("ansible_inventory")
        if ansible_inventory is not None:
            inventory = ansible.inventory.Inventory(ansible_inventory)
        else:
            inventory = ansible.inventory.Inventory()
        return [e.name for e in inventory.get_hosts(pattern=host or "all")]
