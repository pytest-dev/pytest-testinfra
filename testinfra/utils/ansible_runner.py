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

# pylint: disable=import-error,no-name-in-module,no-member
# pylint: disable=unexpected-keyword-arg,no-value-for-parameter
# pylint: disable=arguments-differ

from __future__ import unicode_literals
from __future__ import absolute_import

import pprint


try:
    import ansible
except ImportError:
    raise RuntimeError(
        "You must install ansible package to use the ansible backend")

import ansible.constants
_ansible_version = list(map(int, ansible.__version__.split('.', 2)[:2]))
if _ansible_version[0] == 1:
    import ansible.inventory
    import ansible.runner
    import ansible.utils
elif _ansible_version[0] == 2:
    import ansible.cli.playbook
    import ansible.executor.task_queue_manager
    import ansible.inventory
    import ansible.parsing.dataloader
    import ansible.playbook.play
    import ansible.plugins.callback
    import ansible.utils.vars
    import ansible.vars

try:
    from ansible.module_utils._text import to_bytes
except ImportError:
    from ansible.utils.unicode import to_bytes


__all__ = ['AnsibleRunner', 'to_bytes']


class AnsibleRunnerBase(object):
    _runners = {}

    def __init__(self, host_list=None):
        self.host_list = host_list
        super(AnsibleRunnerBase, self).__init__()

    def get_hosts(self, pattern=None):
        raise NotImplementedError

    def get_variables(self, host):
        raise NotImplementedError

    def run(self, host, module_name, module_args, **kwargs):
        raise NotImplementedError

    @classmethod
    def get_runner(cls, inventory):
        try:
            return cls._runners[inventory]
        except KeyError:
            cls._runners[inventory] = cls(inventory)
            return cls._runners[inventory]


class AnsibleRunnerV1(AnsibleRunnerBase):

    def __init__(self, host_list=None):
        super(AnsibleRunnerV1, self).__init__(host_list)
        self.vault_pass = ansible.utils.read_vault_file(
            ansible.constants.DEFAULT_VAULT_PASSWORD_FILE)
        kwargs = {"vault_password": self.vault_pass}
        if self.host_list is not None:
            kwargs["host_list"] = host_list
        self.inventory = ansible.inventory.Inventory(**kwargs)

    def get_hosts(self, pattern=None):
        return [
            e.name for e in
            self.inventory.get_hosts(pattern=pattern or "all")
        ]

    def get_variables(self, host):
        return self.inventory.get_variables(host)

    def run(self, host, module_name, module_args=None, **kwargs):
        kwargs = kwargs.copy()
        if self.host_list is not None:
            kwargs["host_list"] = self.host_list
        if module_args is not None:
            kwargs["module_args"] = module_args
        result = ansible.runner.Runner(
            pattern=host,
            module_name=module_name,
            vault_pass=self.vault_pass,
            inventory=self.inventory,
            **kwargs).run()
        if host not in result["contacted"]:
            raise RuntimeError("Unexpected error: {}".format(result))
        if result["contacted"][host].get("skipped", False) is True:
            # For consistency with ansible v2 backend
            result["contacted"][host]["failed"] = True
        return result["contacted"][host]


if _ansible_version[0] == 2:
    class Callback(ansible.plugins.callback.CallbackBase):

        def __init__(self, *args, **kwargs):
            self.result = {}
            super(Callback, self).__init__(*args, **kwargs)

        def runner_on_ok(self, host, result):
            self.result = result

        def runner_on_failed(self, host, result, ignore_errors=False):
            self.result = result

        # pylint: disable=no-self-use
        def runner_on_unreachable(self, host, result):
            raise RuntimeError(
                'Host {} is unreachable: {}'.format(
                    host, pprint.pformat(result)),
            )

        def runner_on_skipped(self, host, item=None):
            self.result = {
                'failed': True,
                'msg': 'Skipped. You might want to try check=False',
                'item': item,
            }


class AnsibleRunnerV2(AnsibleRunnerBase):

    def __init__(self, host_list=None):
        super(AnsibleRunnerV2, self).__init__(host_list)
        self.cli = ansible.cli.playbook.PlaybookCLI(None)
        self.cli.options = self.cli.base_parser(
            connect_opts=True,
            meta_opts=True,
            runas_opts=True,
            subset_opts=True,
            check_opts=True,
            inventory_opts=True,
            runtask_opts=True,
            vault_opts=True,
            fork_opts=True,
            module_opts=True,
        ).parse_args([])[0]
        self.cli.normalize_become_options()
        self.cli.options.connection = "smart"
        if _ansible_version[1] >= 4:  # ansible >= 2.4
            self.cli.options.inventory = host_list
            # pylint: disable=protected-access
            self.loader, self.inventory, self.variable_manager = (
                self.cli._play_prereqs(self.cli.options))
        else:  # ansible < 2.4
            self.variable_manager = ansible.vars.VariableManager()
            self.loader = ansible.parsing.dataloader.DataLoader()
            if self.cli.options.vault_password_file:
                vault_pass = self.cli.read_vault_password_file(
                    self.cli.options.vault_password_file, loader=self.loader)
                self.loader.set_vault_password(vault_pass)
            self.inventory = ansible.inventory.Inventory(
                loader=self.loader,
                variable_manager=self.variable_manager,
                host_list=host_list or self.cli.options.inventory,
            )
            self.variable_manager.set_inventory(self.inventory)

    def get_hosts(self, pattern=None):
        return [
            e.name for e in
            self.inventory.get_hosts(pattern=pattern or "all")
        ]

    def get_variables(self, host):
        host = self.inventory.get_host(host)
        if _ansible_version[1] >= 4:  # ansible >= 2.4
            return self.variable_manager.get_vars(host=host)
        # ansible < 2.4
        return self.variable_manager.get_vars(self.loader, host=host)

    def run(self, host, module_name, module_args=None, **kwargs):
        self.cli.options.check = kwargs.get("check", False)
        self.cli.options.become = kwargs.get("become", False)
        action = {"module": module_name}
        if module_args is not None:
            if module_name in ("command", "shell"):
                # Workaround https://github.com/ansible/ansible/issues/13862
                module_args = module_args.replace("=", "\\=")
            action["args"] = module_args
        play = ansible.playbook.play.Play().load({
            "hosts": host,
            "gather_facts": "no",
            "tasks": [{
                "action": action,
            }],
        }, variable_manager=self.variable_manager, loader=self.loader)
        tqm = None
        callback = Callback()
        try:
            tqm = ansible.executor.task_queue_manager.TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.cli.options,
                passwords=None,
                stdout_callback=callback,
            )
            tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

        return callback.result


if _ansible_version[0] == 1:
    AnsibleRunner = AnsibleRunnerV1
elif _ansible_version[0] == 2:
    AnsibleRunner = AnsibleRunnerV2
else:
    raise NotImplementedError(
        "Unhandled ansible version " + ansible.__version__
    )
