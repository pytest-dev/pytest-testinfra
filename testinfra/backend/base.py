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
from __future__ import print_function

import locale
import logging
import pipes
import subprocess

import testinfra.modules

logger = logging.getLogger(__file__)


class CommandResult(object):

    def __init__(
        self, backend, exit_status, stdout_bytes, stderr_bytes, command,
        stdout=None, stderr=None,
    ):
        self.exit_status = exit_status
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
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
            self._stdout = self._backend.decode(self.stdout_bytes)
        return self._stdout

    @property
    def stderr(self):
        if self._stderr is None:
            self._stderr = self._backend.decode(self.stderr_bytes)
        return self._stderr

    def __repr__(self):
        return (
            "CommandResult(command=%s, exit_status=%s, stdout=%s, "
            "stderr=%s)"
        ) % (
            repr(self.command),
            self.exit_status,
            repr(self.stdout_bytes),
            repr(self.stderr_bytes),
        )


class BaseBackend(object):
    NAME = None
    HAS_RUN_SALT = False
    HAS_RUN_ANSIBLE = False

    def __init__(self, hostname, sudo=False, *args, **kwargs):
        for arg in args:
            logger.warning("Ignored argument: %s", arg)
        for key, value in kwargs.items():
            logger.warning("Ignored argument: %s = %s", key, value)
        self._encoding = None
        self._module_cache = {}
        self.hostname = hostname
        self.sudo = sudo
        super(BaseBackend, self).__init__()

    @classmethod
    def get_connection_type(cls):
        return cls.NAME

    def get_hostname(self):
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

    def quote(self, command, *args):
        if args:
            return command % tuple(pipes.quote(a) for a in args)
        else:
            return command

    def get_command(self, command, *args):
        if self.sudo:
            command = self.quote("sudo /bin/sh -c %s", command)
        return self.quote(command, *args)

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
        result = CommandResult(
            self, p.returncode, stdout, stderr, command,
        )
        print("RUN", result)
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

    def get_encoding(self):
        cmd = self.run(
            "python -c 'import locale;print(locale.getpreferredencoding())'")
        if cmd.rc == 0:
            encoding = cmd.stdout_bytes.splitlines()[0].decode("ascii")
        else:
            # Python is not installed, we hope the encoding to be the same as
            # local machine...
            encoding = locale.getpreferredencoding()
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

    def get_module(self, name):
        try:
            module = self._module_cache[name]
        except KeyError:
            module = getattr(testinfra.modules, name).get_module(self)
            self._module_cache[name] = module
        return module
