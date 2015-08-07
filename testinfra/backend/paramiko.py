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
import os

from testinfra.backend import base

try:
    import paramiko
except ImportError:
    HAS_PARAMIKO = False
else:
    HAS_PARAMIKO = True

logger = logging.getLogger("testinfra.backend")


class Bakend(base.BaseBackend):
    _backend_type = "paramiko"

    def __init__(self, hostspec, ssh_config=None, sudo=False, *args, **kwargs):
        self.host, self.user, self.port = self.parse_hostspec(hostspec)
        self.ssh_config = ssh_config
        self.sudo = sudo
        self._client = None
        super(Bakend, self).__init__(*args, **kwargs)

    @property
    def client(self):
        if self._client is None:
            if not HAS_PARAMIKO:
                raise RuntimeError((
                    "You must install paramiko package (pip install paramiko) "
                    "to use the paramiko backend"))
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            cfg = {
                "hostname": self.host,
                "port": int(self.port) if self.port else 22,
                "username": self.user,
            }
            if self.ssh_config:
                ssh_config = paramiko.SSHConfig()
                with open(self.ssh_config) as f:
                    ssh_config.parse(f)

                for key, value in ssh_config.lookup(self.host).items():
                    if key == "hostname":
                        cfg[key] = value
                    elif key == "user":
                        cfg["username"] = value
                    elif key == "port":
                        cfg[key] = int(value)
                    elif key == "identityfile":
                        cfg["key_filename"] = os.path.expanduser(value[0])

            client.connect(**cfg)
            self._client = client
        return self._client

    def run(self, command, *args, **kwargs):
        if self.sudo:
            command = "sudo " + command
        command = self.quote(command, *args)
        chan = self.client.get_transport().open_session()
        logger.info("RUN %s", command)
        command = self.encode(command)
        chan.exec_command(command)
        rc = chan.recv_exit_status()
        stdout = b''.join(chan.makefile('rb'))
        stderr = b''.join(chan.makefile_stderr('rb'))
        return base.CommandResult(self, rc, stdout, stderr, command)
