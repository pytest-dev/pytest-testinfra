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
from __future__ import absolute_import

from testinfra.backend import base

try:
    import salt.client
except ImportError:
    HAS_SALT = False
else:
    HAS_SALT = True


class SaltBackend(base.BaseBackend):
    _backend_type = "salt"

    def __init__(self, host, sudo=False, *args, **kwargs):
        self.host = host
        self._client = None
        self.sudo = sudo
        super(SaltBackend, self).__init__(*args, **kwargs)

    @property
    def client(self):
        if self._client is None:
            if not HAS_SALT:
                raise RuntimeError(
                    "You must install salt package to use the salt backend")
            self._client = salt.client.LocalClient()
        return self._client

    def run(self, command, *args):
        if self.sudo:
            command = "sudo " + command
        command = self.quote(command, *args)
        out = self.run_salt("cmd.run_all", [command])
        return base.CommandResult(
            self, out['retcode'], out['stdout'], out['stderr'], command)

    def run_salt(self, func, args=None):
        return self.client.cmd(self.host, func, args or [])[self.host]
