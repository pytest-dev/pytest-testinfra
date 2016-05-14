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

# pylint: disable=import-error

from __future__ import unicode_literals
from __future__ import absolute_import

try:
    import ansible
except ImportError:
    _has_ansible = False
else:
    _has_ansible = True
    _ansible_major_version = int(ansible.__version__.split(".", 1)[0])
    if _ansible_major_version == 1:
        import ansible.inventory
        import ansible.runner
    elif _ansible_major_version == 2:
        import ansible.executor.task_queue_manager
        import ansible.inventory
        import ansible.parsing.dataloader
        import ansible.playbook.play
        import ansible.plugins.callback
        import ansible.vars


class AnsibleRunnerBase(object):

    def __init__(self, host_list=None):
        self.host_list = host_list
        super(AnsibleRunnerBase, self).__init__()

    def get_hosts(self, pattern=None):
        raise NotImplementedError

    def get_variables(self, host):
        raise NotImplementedError

    def run(self, module_name, module_args, **kwargs):
        raise NotImplementedError


class AnsibleRunnerUnavailable(AnsibleRunnerBase):
    _unavailable = RuntimeError(
        "You must install ansible package to use the ansible backend")

    def get_hosts(self, pattern=None):
        raise self._unavailable

    def get_variables(self, host):
        raise self._unavailable

    def run(self, host, module_name, module_args, **kwargs):
        raise self._unavailable


class AnsibleRunnerV1(AnsibleRunnerBase):

    def __init__(self, host_list=None):
        super(AnsibleRunnerV1, self).__init__(host_list)
        self.inventory = ansible.inventory.Inventory(self.host_list)

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
            **kwargs).run()
        if host not in result["contacted"]:
            raise RuntimeError("Unexpected error: {}".format(result))
        return result["contacted"][host]


class Options(object):

    def __init__(self, **kwargs):
        self.connection = "smart"
        for attr in (
            "module_path", "forks", "remote_user", "private_key_file",
            "ssh_common_args", "ssh_extra_args", "sftp_extra_args",
            "scp_extra_args", "become", "become_method", "become_user",
            "verbosity",
        ):
            setattr(self, attr, None)
        self.check = kwargs.get("check", False)
        super(Options, self).__init__()


if _has_ansible and _ansible_major_version == 2:
    class Callback(ansible.plugins.callback.CallbackBase):

        def __init__(self):
            self.unreachable = {}
            self.contacted = {}

        def runner_on_ok(self, host, result):
            self.contacted[host] = {
                "success": True,
                "result": result,
            }

        def runner_on_failed(self, host, result, ignore_errors=False):
            self.contacted[host] = {
                "success": False,
                "result": result,
            }

        def runner_on_unreachable(self, host, result):
            self.unreachable[host] = result


class AnsibleRunnerV2(AnsibleRunnerBase):

    def __init__(self, host_list=None):
        super(AnsibleRunnerV2, self).__init__(host_list)
        self.variable_manager = ansible.vars.VariableManager()
        self.loader = ansible.parsing.dataloader.DataLoader()
        self.inventory = ansible.inventory.Inventory(
            loader=self.loader,
            variable_manager=self.variable_manager,
            host_list=host_list,
        )
        self.variable_manager.set_inventory(self.inventory)

    def get_hosts(self, pattern=None):
        return [
            e.name for e in
            self.inventory.get_hosts(pattern=pattern or "all")
        ]

    def get_variables(self, host):
        return self.inventory.get_vars(host)

    def run(self, host, module_name, module_args=None, **kwargs):
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
        options = Options(**kwargs)
        callback = Callback()
        try:
            tqm = ansible.executor.task_queue_manager.TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=options,
                passwords=None,
                stdout_callback=callback,
            )
            tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

        if host in callback.unreachable:
            raise RuntimeError(
                "host unreachable: {}".format(callback.unreachable[host]))
        return callback.contacted[host]["result"]

if not _has_ansible:
    AnsibleRunner = AnsibleRunnerUnavailable
elif _ansible_major_version == 1:
    AnsibleRunner = AnsibleRunnerV1
elif _ansible_major_version == 2:
    AnsibleRunner = AnsibleRunnerV2
else:
    raise NotImplementedError(
        "Unhandled ansible version " + ansible.__version__
    )


def get_hosts(host_list=None, pattern=None):
    return AnsibleRunner(host_list).get_hosts(pattern)


def run(host, module_name, module_args=None, host_list=None, **kwargs):
    return AnsibleRunner(host_list).run(
        host, module_name, module_args, **kwargs)


def get_variables(host, host_list=None):
    return AnsibleRunner(host_list).get_variables(host)
