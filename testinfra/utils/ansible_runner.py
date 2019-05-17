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

import fnmatch
import json
import os

from six.moves import configparser

import testinfra
from testinfra.utils import cached_property
from testinfra.utils import check_ip_address
from testinfra.utils import TemporaryDirectory


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
    cmd = 'ansible-inventory --list'
    args = []
    if inventory_file:
        cmd += ' -i %s'
        args += [inventory_file]
    return json.loads(local.check_output(cmd, *args))


def get_ansible_host(config, inventory, host, ssh_config=None,
                     ssh_identity_file=None):
    if is_empty_inventory(inventory):
        return testinfra.get_host('local://')
    hostvars = inventory['_meta'].get('hostvars', {}).get(host, {})
    connection = hostvars.get('ansible_connection', 'ssh')
    if connection not in ('ssh', 'local', 'docker', 'lxc', 'lxd'):
        raise NotImplementedError(
            'unhandled ansible_connection {}'.format(connection))
    if connection == 'lxd':
        connection = 'lxc'
    if connection == 'ssh':
        connection = 'paramiko'
    testinfra_host = hostvars.get('ansible_host', host)
    user = hostvars.get('ansible_user')
    port = hostvars.get('ansible_port')
    kwargs = {}
    if hostvars.get('ansible_become', False):
        kwargs['sudo'] = True
    kwargs['sudo_user'] = hostvars.get('ansible_become_user')
    if ssh_config is not None:
        kwargs['ssh_config'] = ssh_config
    if ssh_identity_file is not None:
        kwargs['ssh_identity_file'] = ssh_identity_file
    if 'ansible_ssh_private_key_file' in hostvars:
        kwargs['ssh_identity_file'] = hostvars[
            'ansible_ssh_private_key_file']
    spec = '{}://'.format(connection)
    if user:
        spec += '{}@'.format(user)
    if check_ip_address(testinfra_host) == 6:
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


class AnsibleRunner(object):
    _runners = {}

    def __init__(self, inventory_file=None):
        self.inventory_file = inventory_file
        self._host_cache = {}
        super(AnsibleRunner, self).__init__()

    def get_hosts(self, pattern="all"):
        inventory = self.inventory
        result = set()
        if is_empty_inventory(inventory):
            # empty inventory should not return any hosts except for localhost
            if pattern == 'localhost':
                result.add('localhost')
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

    def run(self, host, command, **kwargs):
        return self.get_host(host, **kwargs).run(command)

    def run_module(self, host, module_name, module_args, become=False,
                   check=True, **kwargs):
        cmd, args = 'ansible --tree %s', [None]
        if self.inventory_file:
            cmd += ' -i %s'
            args += [self.inventory_file]
        cmd += ' -m %s'
        args += [module_name]
        if module_args:
            cmd += ' --args %s'
            args += [module_args]
        if become:
            cmd += ' --become'
        if check:
            cmd += ' --check'
        cmd += ' %s'
        args += [host]
        with TemporaryDirectory() as d:
            args[0] = d
            out = local.run_expect([0, 2], cmd, *args)
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
