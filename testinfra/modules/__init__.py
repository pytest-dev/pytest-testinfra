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

import importlib

modules = {
    'Ansible': 'ansible:Ansible',
    'Command': 'command:Command',
    'File': 'file:File',
    'Group': 'group:Group',
    'Interface': 'interface:Interface',
    'MountPoint': 'mountpoint:MountPoint',
    'Package': 'package:Package',
    'PipPackage': 'pip:PipPackage',
    'Process': 'process:Process',
    'PuppetResource': 'puppet:PuppetResource',
    'Facter': 'puppet:Facter',
    'Salt': 'salt:Salt',
    'Service': 'service:Service',
    'Socket': 'socket:Socket',
    'Sudo': 'sudo:Sudo',
    'Supervisor': 'supervisor:Supervisor',
    'Sysctl': 'sysctl:Sysctl',
    'SystemInfo': 'systeminfo:SystemInfo',
    'User': 'user:User',
}


def get_module_class(name):
    modname, classname = modules[name].split(':')
    modname = '.'.join([__name__, modname])
    module = importlib.import_module(modname)
    return getattr(module, classname)
