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

import json

from testinfra.modules.base import InstanceModule


def parse_puppet_resource(data):
    """Parse data returned by 'puppet resource'

    $ puppet resource user
    user { 'root':
        ensure  => 'present',
        comment => 'root',
        gid     => '0',
        home    => '/root',
        shell   => '/usr/bin/zsh',
        uid     => '0',
    }
    user { 'sshd':
      ensure => 'present',
      gid    => '65534',
      home   => '/var/run/sshd',
      shell  => '/usr/sbin/nologin',
      uid    => '106',
    }
    [...]
    """

    state = {}
    current = None
    for line in data.splitlines():
        if not current:
            current = line.split("'")[1]
            state[current] = {}
        elif current and line == "}":
            current = None
        elif current:
            key, value = line.split(' => ')
            key = key.strip()
            value = value.split("'")[1]
            state[current][key] = value
    return state


class PuppetResource(InstanceModule):
    """Get puppet resources

    Run ``puppet resource --types`` to get a list of available types.

    >>> PuppetResource("user", "www-data")
    {
        'www-data': {
            'ensure': 'present',
            'comment': 'www-data',
            'gid': '33',
            'home': '/var/www',
            'shell': '/usr/sbin/nologin',
            'uid': '33',
        },
    }
    """

    def __call__(self, resource_type, name=None):
        cmd = "puppet resource %s"
        args = [resource_type]
        if name is not None:
            cmd += " %s"
            args.append(name)
        # TODO(phil): Since puppet 4.0.0 puppet resource has a --to_yaml option
        return parse_puppet_resource(self.check_output(cmd, *args))

    def __repr__(self):
        return "<PuppetResource>"


class Facter(InstanceModule):
    """Get facts with `facter <https://puppetlabs.com/facter>`_

    >>> Facter()
    {
        "operatingsystem": "Debian",
        "kernel": "linux",
        [...]
    }
    >>> Facter("kernelversion", "is_virtual")
    {
      "kernelversion": "3.16.0",
      "is_virtual": "false"
    }
    """

    def __call__(self, *facts):
        cmd = "facter --json --puppet " + " ".join(facts)
        return json.loads(self.check_output(cmd))

    def __repr__(self):
        return "<facter>"
