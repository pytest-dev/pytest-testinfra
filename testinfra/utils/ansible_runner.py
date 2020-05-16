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

import configparser
import fnmatch
import ipaddress
import json
import os
import tempfile


import testinfra
from testinfra.utils import cached_property


__all__ = ['AnsibleRunner']

local = testinfra.get_host('local://')


def get_ansible_config():
    fname = os.environ.get('ANSIBLE_CONFIG')
    if not fname:
        for possible in (
            'ansible.cfg',
            os.path.join(os.path.expanduser('~'), '.ansible.cfg'),
            os.path.join('/', 'etc', 'ansible', 'ansible.cfg'),
        ):
            if os.path.exists(possible):
                fname = possible
                break
    config = configparser.ConfigParser()
    if not fname:
        return config
    config.read(fname)
    return config


def get_ansible_inventory(config, inventory_file):
    # Disable ansible verbosity to avoid
    # https://github.com/ansible/ansible/issues/59973
    cmd = 'ANSIBLE_VERBOSITY=0 ansible-inventory --list'
    args = []
    if inventory_file:
        cmd += ' -i %s'
        args += [inventory_file]
    return json.loads(local.check_output(cmd, *args))


def get_ansible_host(config, inventory, host, ssh_config=None,
                     ssh_identity_file=None):
    if is_empty_inventory(inventory):
        if host == 'localhost':
            return testinfra.get_host('local://')
        return None
    hostvars = inventory['_meta'].get('hostvars', {}).get(host, {})
    connection = hostvars.get('ansible_connection', 'ssh')
    if connection not in (
        'smart', 'ssh', 'paramiko_ssh', 'local', 'docker', 'lxc', 'lxd',
    ):
        # unhandled connection type, must use force_ansible=True
        return None
    connection = {
        'lxd': 'lxc',
        'paramiko_ssh': 'paramiko',
        'smart': 'ssh',
    }.get(connection, connection)
    testinfra_host = hostvars.get('ansible_host', host)
    user = config.get('defaults', 'remote_user', fallback=None)
    if 'ansible_user' in hostvars:
        user = hostvars.get('ansible_user')
    password = hostvars.get('ansible_ssh_pass')
    port = config.get('defaults', 'remote_port', fallback=None)
    if 'ansible_port' in hostvars:
        port = hostvars.get('ansible_port')
    kwargs = {}
    if hostvars.get('ansible_become', False):
        kwargs['sudo'] = True
    kwargs['sudo_user'] = hostvars.get('ansible_become_user')
    if ssh_config is not None:
        kwargs['ssh_config'] = ssh_config
    if ssh_identity_file is not None:
        kwargs['ssh_identity_file'] = ssh_identity_file

    # Support both keys as advertised by Ansible
    if 'ansible_ssh_private_key_file' in hostvars:
        kwargs['ssh_identity_file'] = hostvars[
            'ansible_ssh_private_key_file']
    elif 'ansible_private_key_file' in hostvars:
        kwargs['ssh_identity_file'] = hostvars[
            'ansible_private_key_file']
    kwargs['ssh_extra_args'] = '{} {}'.format(
        hostvars.get('ansible_ssh_common_args', ''),
        hostvars.get('ansible_ssh_extra_args', '')
    ).strip()

    spec = '{}://'.format(connection)

    # Fallback to user:pasword auth when identity file is not used
    if user and password and not kwargs.get('ssh_identity_file'):
        spec += '{}:{}@'.format(user, password)
    elif user:
        spec += '{}@'.format(user)

    try:
        version = ipaddress.ip_address(testinfra_host).version
    except ValueError:
        version = None
    if version == 6:
        spec += '[' + testinfra_host + ']'
    else:
        spec += testinfra_host
    if port:
        spec += ':{}'.format(port)
    return testinfra.get_host(spec, **kwargs)


def itergroup(inventory, group):
    for host in inventory.get(group, {}).get('hosts', []):
        yield host
    for g in inventory.get(group, {}).get('children', []):
        for host in itergroup(inventory, g):
            yield host


def is_empty_inventory(inventory):
    return not any(True for _ in itergroup(inventory, 'all'))


class AnsibleRunner:
    _runners = {}
    _known_options = {
        # Boolean arguments.
        "become": {
            "cli": "--become",
            "type": "boolean",
        },
        "check": {
            "cli": "--check",
            "type": "boolean",
        },
        "diff": {
            "cli": "--diff",
            "type": "boolean",
        },
        "one_line": {
            "cli": "--one-line",
            "type": "boolean",
        },
        # String arguments.
        "become_method": {
            "cli": "--become-method",
            "type": "string",
        },
        "become_user": {
            "cli": "--become-user",
            "type": "string",
        },
        "user": {
            "cli": "--user",
            "type": "string",
        },
        # Arguments serialized as JSON.
        "extra_vars": {
            "cli": "--extra-vars",
            "type": "json",
        },
    }

    def __init__(self, inventory_file=None):
        self.inventory_file = inventory_file
        self._host_cache = {}
        super().__init__()

    def get_hosts(self, pattern="all"):
        inventory = self.inventory
        result = set()
        if is_empty_inventory(inventory):
            # empty inventory should not return any hosts except for localhost
            if pattern == 'localhost':
                result.add('localhost')
            else:
                raise RuntimeError(
                    'No inventory was parsed (missing file ?), '
                    'only implicit localhost is available')
        else:
            for group in inventory:
                groupmatch = fnmatch.fnmatch(group, pattern)
                if groupmatch:
                    result |= set(itergroup(inventory, group))
                for host in inventory[group].get('hosts', []):
                    if fnmatch.fnmatch(host, pattern):
                        result.add(host)
        return sorted(result)

    @cached_property
    def inventory(self):
        return get_ansible_inventory(self.ansible_config, self.inventory_file)

    @cached_property
    def ansible_config(self):
        return get_ansible_config()

    def get_variables(self, host):
        inventory = self.inventory
        # inventory_hostname, group_names and groups are for backward
        # compatibility with testinfra 2.X
        hostvars = inventory['_meta'].get(
            'hostvars', {}).get(host, {})
        hostvars.setdefault('inventory_hostname', host)
        group_names = []
        groups = {}
        for group in sorted(inventory):
            if group == "_meta":
                continue
            groups[group] = sorted(list(itergroup(inventory, group)))
            if group != "all" and host in inventory[group].get('hosts', []):
                group_names.append(group)
        hostvars.setdefault('group_names', group_names)
        hostvars.setdefault('groups', groups)
        return hostvars

    def get_host(self, host, **kwargs):
        try:
            return self._host_cache[host]
        except KeyError:
            self._host_cache[host] = get_ansible_host(
                self.ansible_config, self.inventory, host, **kwargs)
            return self._host_cache[host]

    def options_to_cli(self, options):
        verbose = options.pop("verbose", 0)

        args = {"become": False, "check": True}
        args.update(options)

        cli = []
        cli_args = []
        if verbose:
            cli.append('-' + "v" * verbose)
        for arg_name, value in args.items():
            option = self._known_options[arg_name]
            opt_cli = option["cli"]
            opt_type = option["type"]
            if opt_type == "boolean":
                if value:
                    cli.append(opt_cli)
            elif opt_type == "string":
                cli.append(opt_cli + " %s")
                cli_args.append(value)
            elif opt_type == "json":
                cli.append(opt_cli + " %s")
                value_json = json.dumps(value)
                cli_args.append(value_json)
            else:
                raise TypeError("Unsupported argument type '%s'." % opt_type)
        return " ".join(cli), cli_args

    def run_module(self, host, module_name, module_args, **options):
        cmd, args = 'ansible --tree %s', [None]
        if self.inventory_file:
            cmd += ' -i %s'
            args += [self.inventory_file]
        cmd += ' -m %s'
        args += [module_name]
        if module_args:
            cmd += ' --args %s'
            args += [module_args]
        options_cli, options_args = self.options_to_cli(options)
        if options_cli:
            cmd += ' ' + options_cli
            args.extend(options_args)
        cmd += ' %s'
        args += [host]
        with tempfile.TemporaryDirectory() as d:
            args[0] = d
            out = local.run_expect([0, 2, 8], cmd, *args)
            files = os.listdir(d)
            if not files and 'skipped' in out.stdout.lower():
                return {'failed': True, 'skipped': True,
                        'msg': 'Skipped. You might want to try check=False'}
            if not files:
                raise RuntimeError('Error while running {}: {}'.format(
                    ' '.join(cmd), out))
            with open(os.path.join(d, files[0]), 'r') as f:
                return json.load(f)

    @classmethod
    def get_runner(cls, inventory):
        try:
            return cls._runners[inventory]
        except KeyError:
            cls._runners[inventory] = cls(inventory)
            return cls._runners[inventory]
