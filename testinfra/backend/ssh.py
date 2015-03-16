# -*- coding: utf8 -*-
# Copyright © 2015 Philippe Pepiot
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

from testinfra.backend import local


class SshBackend(local.LocalBackend):

    def __init__(self, hostspec, *args, **kwargs):
        self.host, self.user, self.port = self.parse_hostspec(hostspec)
        super(SshBackend, self).__init__(*args, **kwargs)

    def run(self, command, *args, **kwargs):
        cmd = ["ssh"]
        cmd_args = []
        if self.user:
            cmd.append("-o User=%s")
            cmd_args.append(self.user)
        if self.port:
            cmd.append("-o Port=%s")
            cmd_args.append(self.port)
        cmd.append("%s %s")
        cmd_args.extend([
            self.host,
            self.quote(command, *args)
        ])
        return super(SshBackend, self).run(
            " ".join(cmd), *cmd_args, **kwargs)
