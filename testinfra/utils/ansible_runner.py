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
from testinfra.utils import TemporaryDirectory


__all__ = ['AnsibleRunner']

EMPTY_INVENTORY = {
    "_meta": {
        "hostvars": {}
    },
    "all": {
        "children": [
            "ungrouped"
        ]
    },
    "ungrouped": {}
}
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


def get_ansible_host(config, inventory, host):
    if inventory == EMPTY_INVENTORY:
        return testinfra.get_host('local://')
    hostvars = inventory['_meta'].get('hostvars', {}).get(host, {})
    connection = hostvars.get('ansible_connection', 'ssh')
    if connection not in ('ssh', 'local', 'docker'):
        raise NotImplementedError(
            'unhandled ansible_connection {}'.format(connection))
    if connection == 'ssh':
        connection = 'paramiko'
    testinfra_host = hostvars.get('ansible_host', host)
    user = hostvars.get('ansible_user')
    port = hostvars.get('ansible_port')
    kwargs = {}
    if hostvars.get('ansible_become', False):
        kwargs['sudo'] = True
    kwargs['sudo_user'] = hostvars.get('ansible_become_user')
    if 'ansible_ssh_private_key_file' in hostvars:
        kwargs['ssh_identity_file'] = hostvars[
            'ansible_ssh_private_key_file']
    spec = '{}://'.format(connection)
    if user:
        spec += '{}@'.format(user)
    spec += testinfra_host
    if port:
        spec += ':{}'.format(port)
    return testinfra.get_host(spec, **kwargs)


class AnsibleRunner(object):
    _runners = {}

    def __init__(self, inventory_file=None):
        self.inventory_file = inventory_file
        self._host_cache = {}
        super(AnsibleRunner, self).__init__()

    def get_hosts(self, pattern=None):
        inventory = self.inventory
        result = set()

        def itergroup(group):
            for host in inventory[group].get('hosts', []):
                yield host
            for g in inventory[group].get('children', []):
                for host in itergroup(g):
                    yield host

        if inventory == EMPTY_INVENTORY:
            # use localhost as fallback
            result.add('localhost')
        else:
            for group in inventory:
                groupmatch = fnmatch.fnmatch(group, pattern)
                if groupmatch:
                    result |= set(itergroup(group))
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
        hostvars = inventory['_meta'].get(
            'hostvars', {}).get(host, {})
        hostvars.setdefault('inventory_hostname', host)
        groups = []
        for group in sorted(inventory):
            if group in ('_meta', 'all'):
                continue
            if host in inventory[group].get('hosts', []):
                groups.append(group)
        hostvars.setdefault('group_names', groups)
        return hostvars

    def get_host(self, host):
        try:
            return self._host_cache[host]
        except KeyError:
            self._host_cache[host] = get_ansible_host(
                self.ansible_config, self.inventory, host)
            return self._host_cache[host]

    def run(self, host, command):
        return self.get_host(host).run(command)

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
