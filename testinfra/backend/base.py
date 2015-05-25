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

import locale
import pipes


ENCODING = locale.getpreferredencoding()


class CommandResult(object):

    def __init__(self, exit_status, stdout_bytes, stderr_bytes, command):
        self.exit_status = exit_status
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self._stdout = None
        self._stderr = None
        self.command = command
        super(CommandResult, self).__init__()

    @property
    def rc(self):
        return self.exit_status

    @property
    def stdout(self):
        if self._stdout is None:
            self._stdout = self.stdout_bytes.decode(ENCODING)
        return self._stdout

    @property
    def stderr(self):
        if self._stderr is None:
            self._stderr = self.stderr_bytes.decode(ENCODING)
        return self._stderr

    def __repr__(self):
        return (
            "CommandResult(exit_status=%s, stdout=%s, "
            "stderr=%s, command=%s)"
        ) % (
            self.exit_status,
            repr(self.stdout_bytes),
            repr(self.stderr_bytes),
            repr(self.command),
        )


class BaseBackend(object):
    _backend_type = None

    def __init__(self, *args, **kwargs):
        if args or kwargs:
            raise RuntimeError("Unexpected arguments %s %s" % (args, kwargs))
        super(BaseBackend, self).__init__()

    def quote(self, command, *args):
        if args:
            return command % tuple(pipes.quote(a) for a in args)
        else:
            return command

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

    def run(self, command, *args):
        raise NotImplementedError

    @classmethod
    def get_backend_type(cls):
        if cls._backend_type is None:
            raise RuntimeError("No backend type")
        return cls._backend_type
