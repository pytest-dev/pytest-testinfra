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

import locale
import logging
import pipes
import subprocess

import testinfra.modules

logger = logging.getLogger("testinfra")


class CommandResult(object):

    def __init__(
        self, backend, exit_status, command, stdout_bytes,
        stderr_bytes, stdout=None, stderr=None,
    ):
        self.exit_status = exit_status
        self._stdout_bytes = stdout_bytes
        self._stderr_bytes = stderr_bytes
        self._stdout = stdout
        self._stderr = stderr
        self.command = command
        self._backend = backend
        super(CommandResult, self).__init__()

    @property
    def rc(self):
        return self.exit_status

    @property
    def stdout(self):
        if self._stdout is None:
            self._stdout = self._backend.decode(self._stdout_bytes)
        return self._stdout

    @property
    def stderr(self):
        if self._stderr is None:
            self._stderr = self._backend.decode(self._stderr_bytes)
        return self._stderr

    @property
    def stdout_bytes(self):
        if self._stdout_bytes is None:
            self._stdout_bytes = self._backend.encode(self._stdout)
        return self._stdout_bytes

    @property
    def stderr_bytes(self):
        if self._stderr_bytes is None:
            self._stderr_bytes = self._backend.encode(self._stderr)
        return self._stderr_bytes

    def __repr__(self):
        return (
            "CommandResult(command=%s, exit_status=%s, stdout=%s, "
            "stderr=%s)"
        ) % (
            repr(self.command),
            self.exit_status,
            repr(self._stdout_bytes or self._stdout),
            repr(self._stderr_bytes or self._stderr),
        )


class BaseBackend(object):
    """Represent the connection to the remote or local system"""
    NAME = None
    HAS_RUN_SALT = False
    HAS_RUN_ANSIBLE = False

    def __init__(self, hostname, sudo=False, sudo_user=None, *args, **kwargs):
        self._encoding = None
        self._module_cache = {}
        self.hostname = hostname
        self.sudo = sudo
        self.sudo_user = sudo_user
        super(BaseBackend, self).__init__()

    @classmethod
    def get_connection_type(cls):
        """Return the connection backend used as string.

        Can be local, paramiko, ssh, docker, salt or ansible
        """
        return cls.NAME

    def get_hostname(self):
        """Return the hostname (for testinfra) of the remote or local system


        Can be useful for multi-hosts tests:

        Example:
        ::

            import requests


            def test(TestinfraBackend):
                host = TestinfraBackend.get_hostname()
                response = requests.get("http://" + host)
                assert response.status_code == 200


        ::

            $ testinfra --hosts=server1,server2 test.py

            test.py::test[paramiko://server1] PASSED
            test.py::test[paramiko://server2] PASSED
        """
        return self.hostname

    def get_pytest_id(self):
        return self.get_connection_type() + "://" + self.get_hostname()

    @classmethod
    def get_hosts(cls, host, **kwargs):
        if host is None:
            raise RuntimeError(
                "One or more hosts is required with the %s backend" % (
                    cls.get_connection_type(),),
            )
        return [host]

    @staticmethod
    def quote(command, *args):
        if args:
            return command % tuple(pipes.quote(a) for a in args)
        else:
            return command

    def get_sudo_command(self, command, sudo_user):
        if sudo_user is None:
            return self.quote("sudo /bin/sh -c %s", command)
        else:
            return self.quote(
                "sudo -u %s /bin/sh -c %s", sudo_user, command)

    def get_command(self, command, *args):
        command = self.quote(command, *args)
        if self.sudo:
            command = self.get_sudo_command(command, self.sudo_user)
        return command

    def run(self, command, *args, **kwargs):
        raise NotImplementedError

    def run_local(self, command, *args):
        command = self.quote(command, *args)
        command = self.encode(command)
        p = subprocess.Popen(
            command, shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        result = self.result(p.returncode, command, stdout, stderr)
        return result

    @staticmethod
    def parse_hostspec(hostspec):
        host = hostspec
        user = None
        port = None
        if "@" in host:
            user, host = host.split("@", 1)
        if ":" in host:
            host, port = host.split(":", 1)
        return host, user, port

    @staticmethod
    def parse_containerspec(containerspec):
        name = containerspec
        user = None
        if "@" in name:
            user, name = name.split("@", 1)
        return name, user

    def get_encoding(self):
        cmd = self.run(
            "python -c 'import locale;print(locale.getpreferredencoding())'")
        if cmd.rc == 0:
            encoding = cmd.stdout_bytes.splitlines()[0].decode("ascii")
        else:
            # Python is not installed, we hope the encoding to be the same as
            # local machine...
            encoding = locale.getpreferredencoding()
        if encoding == "ANSI_X3.4-1968":
            # Workaround defaut encoding ascii without LANG set
            encoding = "UTF-8"
        return encoding

    @property
    def encoding(self):
        if self._encoding is None:
            self._encoding = self.get_encoding()
        return self._encoding

    def decode(self, data):
        try:
            return data.decode("ascii")
        except UnicodeDecodeError:
            return data.decode(self.encoding)

    def encode(self, data):
        try:
            return data.encode("ascii")
        except UnicodeEncodeError:
            return data.encode(self.encoding)

    def result(self, *args, **kwargs):
        result = CommandResult(self, *args, **kwargs)
        logger.info("RUN %s", result)
        return result

    def __getattr__(self, attr):
        return self.get_module(attr)

    def get_module(self, name):
        """Return the testinfra module adapted to the current backend

        ::

            def test(Package):
                [...]

            # Is equivalent to
            def test(TestinfraBackend):
                Package = TestinfraBackend.get_module("Package")

        """
        try:
            module = self._module_cache[name]
        except KeyError:
            module = testinfra.modules.get_module_class(name).get_module(self)
            self._module_cache[name] = module
        return module
