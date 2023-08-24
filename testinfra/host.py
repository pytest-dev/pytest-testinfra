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

import functools
import os
from collections.abc import Iterable
from typing import Any

import testinfra.backend
import testinfra.backend.base
import testinfra.modules
import testinfra.modules.base


class Host:
    _host_cache: dict[tuple[str, frozenset[tuple[str, Any]]], "Host"] = {}
    _hosts_cache: dict[
        tuple[frozenset[str], frozenset[tuple[str, Any]]], list["Host"]
    ] = {}

    def __init__(self, backend: testinfra.backend.base.BaseBackend):
        self.backend = backend
        super().__init__()

    def __repr__(self) -> str:
        return "<testinfra.host.Host {}>".format(self.backend.get_pytest_id())

    @functools.cached_property
    def has_command_v(self) -> bool:
        """Return True if `command -v` is available"""
        return self.run("command -v command").rc == 0

    def exists(self, command: str) -> bool:
        """Return True if given command exist in $PATH"""
        if self.has_command_v:
            out = self.run("command -v %s", command)
        else:
            out = self.run_expect([0, 1], "which %s", command)
        return out.rc == 0

    def find_command(
        self, command: str, extrapaths: Iterable[str] = ("/sbin", "/usr/sbin")
    ) -> str:
        """Return path of given command

        raise ValueError if command cannot be found
        """
        if self.has_command_v:
            out = self.run("command -v %s", command)
        else:
            out = self.run_expect([0, 1], "which %s", command)
        if out.rc == 0:
            return out.stdout.rstrip("\r\n")
        for basedir in extrapaths:
            path = os.path.join(basedir, command)
            if self.exists(path):
                return path
        raise ValueError('cannot find "{}" command'.format(command))

    def run(
        self, command: str, *args: str, **kwargs: Any
    ) -> testinfra.backend.base.CommandResult:
        """Run given command and return rc (exit status), stdout and stderr

        >>> cmd = host.run("ls -l /etc/passwd")
        >>> cmd.rc
        0
        >>> cmd.stdout
        '-rw-r--r-- 1 root root 1790 Feb 11 00:28 /etc/passwd\\n'
        >>> cmd.stderr
        ''
        >>> cmd.succeeded
        True
        >>> cmd.failed
        False


        Good practice: always use shell arguments quoting to avoid shell
        injection


        >>> cmd = host.run("ls -l -- %s", "/;echo inject")
        CommandResult(
            rc=2, stdout='',
            stderr=(
              'ls: cannot access /;echo inject: No such file or directory\\n'),
            command="ls -l '/;echo inject'")
        """
        return self.backend.run(command, *args, **kwargs)

    def run_expect(
        self, expected: list[int], command: str, *args: str, **kwargs: Any
    ) -> testinfra.backend.base.CommandResult:
        """Run command and check it return an expected exit status

        :param expected: A list of expected exit status
        :raises: AssertionError
        """
        __tracebackhide__ = True
        out = self.run(command, *args, **kwargs)
        assert out.rc in expected, "Unexpected exit code {} for {}".format(out.rc, out)
        return out

    def run_test(
        self, command: str, *args: str, **kwargs: Any
    ) -> testinfra.backend.base.CommandResult:
        """Run command and check it return an exit status of 0 or 1

        :raises: AssertionError
        """
        return self.run_expect([0, 1], command, *args, **kwargs)

    def check_output(self, command: str, *args: str, **kwargs: Any) -> str:
        """Get stdout of a command which has run successfully

        :returns: stdout without trailing newline
        :raises: AssertionError
        """
        __tracebackhide__ = True
        out = self.run(command, *args, **kwargs)
        assert out.rc == 0, "Unexpected exit code {} for {}".format(out.rc, out)
        return out.stdout.rstrip("\r\n")

    def __getattr__(self, name: str) -> type[testinfra.modules.base.Module]:
        if name in testinfra.modules.modules:
            module_class = testinfra.modules.get_module_class(name)
            obj = module_class.get_module(self)
            setattr(self, name, obj)
            return obj
        raise AttributeError(
            "'{}' object has no attribute '{}'".format(self.__class__.__name__, name)
        )

    @classmethod
    def get_host(cls, hostspec: str, **kwargs: Any) -> "Host":
        """Return a Host instance from `hostspec`

        `hostspec` should be like
        `<backend_type>://<name>?param1=value1&param2=value2`

        Params can also be passed in `**kwargs` (eg. get_host("local://",
        sudo=True) is equivalent to get_host("local://?sudo=true"))

        Examples::

        >>> get_host("local://", sudo=True)
        >>> get_host("paramiko://user@host", ssh_config="/path/my_ssh_config")
        >>> get_host("ansible://all?ansible_inventory=/etc/ansible/inventory")
        """
        key = (hostspec, frozenset(kwargs.items()))
        cache = cls._host_cache
        if key not in cache:
            backend = testinfra.backend.get_backend(hostspec, **kwargs)
            cache[key] = host = cls(backend)
            backend.set_host(host)
        return cache[key]

    @classmethod
    def get_hosts(cls, hosts: Iterable[str], **kwargs: Any) -> list["Host"]:
        key = (frozenset(hosts), frozenset(kwargs.items()))
        cache = cls._hosts_cache
        if key not in cache:
            cache[key] = []
            for backend in testinfra.backend.get_backends(hosts, **kwargs):
                host = cls(backend)
                backend.set_host(host)
                cache[key].append(host)
        return cache[key]


get_host = Host.get_host
get_hosts = Host.get_hosts
