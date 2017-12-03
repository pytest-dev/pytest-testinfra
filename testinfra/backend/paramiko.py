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
from testinfra.utils import cached_property


class IgnorePolicy(paramiko.MissingHostKeyPolicy):
    """Policy for ignoring missing host key."""
    def missing_host_key(self, client, hostname, key):
        pass


class ParamikoBackend(base.BaseBackend):
    NAME = "paramiko"

    def __init__(
            self, hostspec, ssh_config=None, ssh_identity_file=None,
            *args, **kwargs):
        self.host = self.parse_hostspec(hostspec)
        self.ssh_config = ssh_config
        self.ssh_identity_file = ssh_identity_file
        self.get_pty = False
        super(ParamikoBackend, self).__init__(self.host.name, *args, **kwargs)

    @cached_property
    def client(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        cfg = {
            "hostname": self.host.name,
            "port": int(self.host.port) if self.host.port else 22,
            "username": self.host.user,
        }
        if self.ssh_config:
            ssh_config = paramiko.SSHConfig()
            with open(self.ssh_config) as f:
                ssh_config.parse(f)

            for key, value in ssh_config.lookup(self.host.name).items():
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
                elif key == "requesttty":
                    if cfg[key] in ('yes', 'force'):
                        self.get_pty = True
        if self.ssh_identity_file:
            cfg["key_filename"] = self.ssh_identity_file
        client.connect(**cfg)
        return client

    def _exec_command(self, command):
        chan = self.client.get_transport().open_session()
        if self.get_pty:
            chan.get_pty()
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
                del self.client
                rc, stdout, stderr = self._exec_command(command)
            else:
                raise

        return self.result(rc, command, stdout, stderr)
