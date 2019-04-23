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

import json
import os
import shutil
import subprocess
import tempfile
import yaml


# the real ansible-runner
import ansible_runner


__all__ = ['AnsibleRunner']


class AnsibleInventoryException(Exception):
    def __init__(self, message):
        super(AnsibleInventoryException, self).__init__(message)
        self.message = message


class AnsibleRunnerV2(object):

    # testinfra api
    _runners = {}

    # testinfra api
    host_list = None

    # variable cache
    variables = {}

    def __init__(self, host_list=None):
        # host_list is the list of inventory files, aka -i
        self.host_list = host_list

    @classmethod
    def get_runner(cls, inventory):
        # stores a copy of the runner in a dict keyed by inv
        if inventory not in cls._runners:
            cls._runners[inventory] = cls(inventory)
        return cls._runners[inventory]

    def fetch_inventory(self, host=None):
        '''Helper function for ansible-inventory'''

        cmd = [
            'ansible-inventory',
            '-i',
            self.host_list
        ]
        if host is not None:
            cmd.append('--host=%s' % host)
        else:
            cmd.append('--list')

        try:
            so = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            raise AnsibleInventoryException(e)

        try:
            inv = json.loads(so)
        except json.JSONDecodeError as e:
            raise AnsibleInventoryException(e)

        return inv

    def get_hosts(self, pattern=None):
        '''Return a list of host names from inventory via the pattern'''
        inv = self.fetch_inventory()
        return list(inv['_meta']['hostvars'].keys())

    def get_variables(self, host, refresh=True):
        '''Get a mixture of inventory vars and magic vars'''

        if host not in self.variables or refresh:

            _vars = self.variables.get(host, {})

            # inventory vars
            _vars.update(self.fetch_inventory(host=host))

            # this is a hack to get the magic vars
            res = self.run(host, 'debug', 'var=hostvars')
            _vars.update(res.get('hostvars', {}).get(host, {}))

            # one of the unit tests insist this should be returned
            _vars['inventory_hostname'] = host
            self.variables[host] = _vars

        return self.variables[host]

    def run(self, host, module_name, module_args=None, **kwargs):
        '''Invokes a single module on a single host and returns dict results'''

        # runner must have a directory based payload
        with tempfile.TemporaryDirectory(prefix='runner.data.') as data_dir:

            # runner must have an inventory file
            inv_dir = os.path.join(data_dir, 'inventory')
            os.makedirs(inv_dir)
            shutil.copy(
                self.host_list,
                os.path.join(inv_dir, os.path.basename(self.host_list))
            )

            # molecule inventories use lookups
            this_env = os.environ.copy()
            this_env['ANSIBLE_NOCOLOR'] = "1"
            env_keys = list(this_env.keys())
            for ekey in env_keys:
                if not ekey.startswith('MOLECULE'):
                    this_env.pop(ekey)
            env_dir = os.path.join(data_dir, 'env')
            if not os.path.exists(env_dir):
                os.makedirs(env_dir)
            with open(os.path.join(env_dir, 'envvars'), 'w') as f:
                f.write('---\n')
                f.write(yaml.dump(this_env))

            # build the kwarg payload ansible-runner requires
            runner_kwargs = {
                'private_data_dir': data_dir,
                'host_pattern': host,
                'module': module_name,
                'module_args': module_args,
                'json_mode': True,
            }

            # ansible-runner does not have kwargs for these
            for opt in ['become', 'check']:
                if kwargs.get(opt, False):
                    if 'cmdline' not in runner_kwargs:
                        runner_kwargs['cmdline'] = '--%s' % opt
                    else:
                        runner_kwargs['cmdline'] += ' --%s' % opt

            return AnsibleRunnerV2.call_runner(runner_kwargs, host)

    @staticmethod
    def call_runner(runner_kwargs, host):
        # invoke ansible-runer -> ansible adhoc
        r = ansible_runner.run(**runner_kwargs)
        events = r.host_events(host)

        # a "significant" event is the event that has the task result
        significant_event = None
        for event in events:
            # looking for a runnner_on_ok or runner_on_!start
            if event['event'] == 'runner_on_start':
                continue
            if event['event'].startswith('runner_on'):
                significant_event = event.get('event_data', {}).get('res')
                break

        if significant_event:
            return significant_event

        return {}


AnsibleRunner = AnsibleRunnerV2
