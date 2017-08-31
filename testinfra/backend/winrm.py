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

try:
    import winrm
except ImportError:
    raise RuntimeError((
        "You must install the pywinrm package (pip install pywinrm) "
        "to use the winrm backend"))

import winrm.protocol


class WinRMBackend(base.BaseBackend):
    """Run command through winrm command"""
    NAME = "winrm"

    def __init__(self, hostspec, password=None, ssl=True, verify_ssl=True,
                 transport='ntlm', *args, **kwargs):
        self.host = self.parse_hostspec(hostspec)
        self.password = password
        self.ssl = ssl
        self.verify_ssl = verify_ssl
        self.transport = transport
        super(WinRMBackend, self).__init__(self.host.name, *args, **kwargs)

    def run(self, command, *args, **kwargs):
        return self.run_winrm(self.get_command(command, *args))

    def run_winrm(self, command, *args):
        conn_args = {
            'endpoint': '{proto}://{host}{port}/wsman'.format(
                proto='https' if self.ssl else 'http',
                host=self.host.name,
                port=':{}'.format(self.host.port) if self.host.port else ''
            ),
            'transport': self.transport,
            'username': self.host.user,
            'password': self.password,
        }

        if self.verify_ssl is False:
            conn_args['server_cert_validation'] = 'ignore'

        p = winrm.protocol.Protocol(**conn_args)
        shell_id = p.open_shell()
        command_id = p.run_command(shell_id, command, *args)
        stdout, stderr, rc = p.get_command_output(shell_id, command_id)
        p.cleanup_command(shell_id, command_id)
        p.close_shell(shell_id)
        return self.result(rc, command, stdout, stderr)
