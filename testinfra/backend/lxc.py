# -*- coding: utf8 -*-
# Copyright © 2016 Andrei Pashkin
#
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


class LXCBackend(base.BaseBackend):
    NAME = "lxc"

    def __init__(self, container, *args, **kwargs):
        self.container = container
        super(LXCBackend, self).__init__(self.container, *args, **kwargs)

    def run(self, command, *args, **kwargs):
        command = self.get_command(command, *args)
        template = 'lxc-attach --name %s -- /bin/sh -c %s'
        if self.sudo:
            template = 'sudo ' + template
        out = self.run_local(template, self.container, command)
        out.command = self.encode(command)
        return out
