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

import base64

from testinfra.backend import base


class SshBackend(base.BaseBackend):
    """Run command through ssh command"""
    NAME = "ssh"

    def __init__(self, hostspec, ssh_config=None, ssh_identity_file=None,
                 *args, **kwargs):
        self.host = self.parse_hostspec(hostspec)
        self.ssh_config = ssh_config
        self.ssh_identity_file = ssh_identity_file
        super(SshBackend, self).__init__(self.host.name, *args, **kwargs)

    def run(self, command, *args, **kwargs):
        return self.run_ssh(self.get_command(command, *args))

    def run_ssh(self, command):
        cmd = ["ssh"]
        cmd_args = []
        if self.ssh_config:
            cmd.append("-F %s")
            cmd_args.append(self.ssh_config)
        if self.host.user:
            cmd.append("-o User=%s")
            cmd_args.append(self.host.user)
        if self.host.port:
            cmd.append("-o Port=%s")
            cmd_args.append(self.host.port)
        if self.ssh_identity_file:
            cmd.append("-i %s")
            cmd_args.append(self.ssh_identity_file)
        cmd.append("%s %s")
        cmd_args.extend([self.host.name, command])
        out = self.run_local(
            " ".join(cmd), *cmd_args)
        out.command = self.encode(command)
        return out


class SafeSshBackend(SshBackend):
    """Run command using ssh command but try to get a more sane output

    When using ssh (or a potentially bugged wrapper) additional output can be
    added in stdout/stderr and exit status may not be propagate correctly

    To avoid that kind of bugs, we wrap the command to have an output like
    this:

    TESTINFRA_START;EXIT_STATUS;STDOUT;STDERR;TESTINFRA_END

    where STDOUT/STDERR are base64 encoded, then we parse that magic string to
    get sanes variables
    """
    NAME = "safe-ssh"

    def run(self, command, *args, **kwargs):
        orig_command = self.get_command(command, *args)

        out = self.run_ssh((
            '''of=$(mktemp)&&ef=$(mktemp)&&%s >$of 2>$ef; r=$?;'''
            '''echo "TESTINFRA_START;$r;$(base64 < $of);$(base64 < $ef);'''
            '''TESTINFRA_END";rm -f $of $ef''') % (orig_command,))

        start = out.stdout.find("TESTINFRA_START;") + len("TESTINFRA_START;")
        end = out.stdout.find("TESTINFRA_END") - 1
        rc, stdout, stderr = out.stdout[start:end].split(";")
        rc = int(rc)
        stdout = base64.b64decode(stdout)
        stderr = base64.b64decode(stderr)
        return self.result(rc, self.encode(orig_command), stdout, stderr)
