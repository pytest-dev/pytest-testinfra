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

import os

try:
    import paramiko
except ImportError:
    raise RuntimeError((
        "You must install paramiko package (pip install paramiko) "
        "to use the paramiko backend"))

import paramiko.ssh_exception

from testinfra.backend import base


class IgnorePolicy(paramiko.MissingHostKeyPolicy):
    """Policy for ignoring missing host key."""
    def missing_host_key(self, client, hostname, key):
        pass


class ParamikoBackend(base.BaseBackend):
    NAME = "paramiko"

    def __init__(self, hostspec, ssh_config=None, *args, **kwargs):
        self.host, self.user, self.port = self.parse_hostspec(hostspec)
        self.ssh_config = ssh_config
        self._client = None
        super(ParamikoBackend, self).__init__(self.host, *args, **kwargs)

    @property
    def client(self):
        if self._client is None:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            cfg = {
                "hostname": self.host,
                "port": int(self.port) if self.port else 22,
                "username": self.user,
            }
            if self.ssh_config:
                ssh_config = paramiko.SSHConfig()
                with open(os.path.expanduser(self.ssh_config)) as f:
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
                    elif key == "stricthostkeychecking" and value == "no":
                        client.set_missing_host_key_policy(IgnorePolicy())

            client.connect(**cfg)
            self._client = client
        return self._client

    def _exec_command(self, command):
        chan = self.client.get_transport().open_session()
        chan.exec_command(command)
        rc = chan.recv_exit_status()
        stdout = b''.join(chan.makefile('rb'))
        stderr = b''.join(chan.makefile_stderr('rb'))
        return rc, stdout, stderr

    def run(self, command, *args, **kwargs):
        command = self.get_command(command, *args)
        command = self.encode(command)
        try:
            rc, stdout, stderr = self._exec_command(command)
        except paramiko.ssh_exception.SSHException:
            if not self.client.get_transport().is_active():
                # try to reinit connection (once)
                self._client = None
                rc, stdout, stderr = self._exec_command(command)
            else:
                raise

        return self.result(rc, command, stdout, stderr)
