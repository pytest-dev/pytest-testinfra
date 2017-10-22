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

import os.path


class Module(object):
    _host = None

    def _find_command(self, command, paths=('/sbin', '/usr/sbin')):
        if self._host.exists(command):
            return command
        for basedir in paths:
            path = os.path.join(basedir, command)
            if self._host.exists(path):
                return path
        raise RuntimeError('Cannot find "%s" command' % (command,))

    @classmethod
    def get_module(cls, _host):
        klass = cls.get_module_class(_host)
        return type(klass.__name__, (klass,), {
            "_host": _host,
            "run": _host.run,
            "run_expect": _host.run_expect,
            "run_test": _host.run_test,
            "check_output": _host.check_output,
        })

    @classmethod
    def get_module_class(cls, host):
        return cls


class InstanceModule(Module):

    @classmethod
    def get_module(cls, _host):
        klass = super(InstanceModule, cls).get_module(_host)
        return klass()
