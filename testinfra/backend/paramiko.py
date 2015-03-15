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

import logging
from testinfra.backend import base

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

logger = logging.getLogger("testinfra.backend")


class ParamikoBakend(base.BaseBackend):

    def __init__(self, host, user="root", *args, **kwargs):
        self.host = host
        self.user = user
        self._client = None
        super(ParamikoBakend, self).__init__(*args, **kwargs)

    @property
    def client(self):
        if self._client is None:
            if not HAS_PARAMIKO:
                raise RuntimeError((
                    "You must install paramiko package (pip install paramiko) "
                    "to use the paramiko backend"))
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(self.host, username=self.user)
            self._client = client
        return self._client

    def run(self, command, *args, **kwargs):
        command = self.quote(command, *args)
        chan = self.client.get_transport().open_session()
        logger.info("RUN %s", command)
        chan.exec_command(command)
        rc = chan.recv_exit_status()
        stdout = ''.join(chan.makefile('rb'))
        stderr = ''.join(chan.makefile_stderr('rb'))
        return base.CommandResult(rc, stdout, stderr, command)
