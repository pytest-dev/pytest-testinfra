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

from testinfra.backend import base


class LxcBackend(base.BaseBackend):
    NAME = "lxc"

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.shell = kwargs.get('shell', '/bin/sh -c')
        super(LxcBackend, self).__init__(self.name, *args, **kwargs)

    def run(self, command, *args, **kwargs):
        cmd = self.get_command(command, *args)
        out = self.run_local("lxc exec %s --mode=non-interactive -- "
                             "{shell} %s".format(shell=self.shell),
                             self.name, cmd)
        out.command = self.encode(cmd)
        return out
