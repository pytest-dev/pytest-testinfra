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

import abc
import dataclasses
import locale
import logging
import shlex
import subprocess
import urllib.parse
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    import testinfra.host

logger = logging.getLogger("testinfra")


@dataclasses.dataclass
class HostSpec:
    name: str
    port: Optional[str]
    user: Optional[str]
    password: Optional[str]


@dataclasses.dataclass
class CommandResult:
    """Object that encapsulates all returned details of the command execution.

    Example:

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
    """

    backend: "BaseBackend"
    exit_status: int
    command: bytes
    _stdout: Union[str, bytes]
    _stderr: Union[str, bytes]

    @property
    def succeeded(self) -> bool:
        """Returns whether the command was successful

        >>> host.run("true").succeeded
        True
        """
        return self.exit_status == 0

    @property
    def failed(self) -> bool:
        """Returns whether the command failed

        >>> host.run("false").failed
        True
        """
        return self.exit_status != 0

    @property
    def rc(self) -> int:
        """Gets the returncode of a command

        >>> host.run("true").rc
        0
        """
        return self.exit_status

    @property
    def stdout(self) -> str:
        """Gets standard output (stdout) stream of an executed command

        >>> host.run("mkdir -v new_directory").stdout
        mkdir: created directory 'new_directory'
        """
        if isinstance(self._stdout, bytes):
            return self.backend.decode(self._stdout)
        return self._stdout

    @property
    def stderr(self) -> str:
        """Gets standard error (stderr) stream of an executed command

        >>> host.run("mkdir new_directory").stderr
        mkdir: cannot create directory 'new_directory': File exists
        """
        if isinstance(self._stderr, bytes):
            return self.backend.decode(self._stderr)
        return self._stderr

    @property
    def stdout_bytes(self) -> bytes:
        """Gets standard output (stdout) stream of an executed command as bytes

        >>> host.run("mkdir -v new_directory").stdout_bytes
        b"mkdir: created directory 'new_directory'"
        """
        if isinstance(self._stdout, str):
            return self.backend.encode(self._stdout)
        return self._stdout

    @property
    def stderr_bytes(self) -> bytes:
        """Gets standard error (stderr) stream of an executed command as bytes

        >>> host.run("mkdir new_directory").stderr_bytes
        b"mkdir: cannot create directory 'new_directory': File exists"
        """
        if isinstance(self._stderr, str):
            return self.backend.encode(self._stderr)
        return self._stderr


class BaseBackend(metaclass=abc.ABCMeta):
    """Represent the connection to the remote or local system"""

    HAS_RUN_SALT = False
    HAS_RUN_ANSIBLE = False
    NAME: str

    def __init__(
        self,
        hostname: str,
        sudo: bool = False,
        sudo_user: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ):
        self._encoding: Optional[str] = None
        self._host: Optional["testinfra.host.Host"] = None
        self.hostname = hostname
        self.sudo = sudo
        self.sudo_user = sudo_user
        super().__init__()

    def set_host(self, host: "testinfra.host.Host") -> None:
        self._host = host

    @classmethod
    def get_connection_type(cls) -> str:
        """Return the connection backend used as string.

        Can be local, paramiko, ssh, docker, salt or ansible
        """
        return cls.NAME

    def get_hostname(self) -> str:
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

    def get_pytest_id(self) -> str:
        return self.get_connection_type() + "://" + self.get_hostname()

    @classmethod
    def get_hosts(cls, host: str, **kwargs: Any) -> list[str]:
        if host is None:
            raise RuntimeError(
                "One or more hosts is required with the {} backend".format(
                    cls.get_connection_type()
                )
            )
        return [host]

    @staticmethod
    def quote(command: str, *args: str) -> str:
        if args:
            return command % tuple(shlex.quote(a) for a in args)  # noqa: S001
        return command

    def get_sudo_command(self, command: str, sudo_user: Optional[str]) -> str:
        if sudo_user is None:
            return self.quote("sudo /bin/sh -c %s", command)
        return self.quote("sudo -u %s /bin/sh -c %s", sudo_user, command)

    def get_command(self, command: str, *args: str) -> str:
        command = self.quote(command, *args)
        if self.sudo:
            command = self.get_sudo_command(command, self.sudo_user)
        return command

    def run(self, command: str, *args: str, **kwargs: Any) -> CommandResult:
        raise NotImplementedError

    def run_local(self, command: str, *args: str) -> CommandResult:
        command = self.quote(command, *args)
        cmd = self.encode(command)
        p = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        result = self.result(p.returncode, cmd, stdout, stderr)
        return result

    @staticmethod
    def parse_hostspec(hostspec: str) -> HostSpec:
        name = hostspec
        port = None
        user = None
        password = None
        if "@" in name:
            user, name = name.split("@", 1)
            if ":" in user:
                user, password = user.split(":", 1)
        # A literal IPv6 address might be like
        #  [fe80:0::a:b:c]:80
        # thus, below in words; if this starts with a '[' assume it
        # encloses an ipv6 address with a closing ']', with a possible
        # trailing port after a colon
        if name.startswith("["):
            name, port = name.split("]")
            name = name[1:]
            if port.startswith(":"):
                port = port[1:]
            else:
                port = None
        else:
            if ":" in name:
                name, port = name.split(":", 1)
        name = urllib.parse.unquote(name)
        if user is not None:
            user = urllib.parse.unquote(user)
        if password is not None:
            password = urllib.parse.unquote(password)
        return HostSpec(name, port, user, password)

    @staticmethod
    def parse_containerspec(containerspec: str) -> tuple[str, Optional[str]]:
        name = containerspec
        user = None
        if "@" in name:
            user, name = name.split("@", 1)
        return name, user

    def get_encoding(self) -> str:
        encoding = None
        for python in ("python3", "python"):
            cmd = self.run(
                "%s -c 'import locale;print(locale.getpreferredencoding())'",
                python,
                encoding=None,
            )
            if cmd.rc == 0:
                encoding = cmd.stdout_bytes.splitlines()[0].decode("ascii")
                break
        # Python is not installed, we hope the encoding to be the same as
        # local machine...
        if not encoding:
            encoding = locale.getpreferredencoding()
        if encoding == "ANSI_X3.4-1968":
            # Workaround default encoding ascii without LANG set
            encoding = "UTF-8"
        return encoding

    @property
    def encoding(self) -> str:
        if self._encoding is None:
            self._encoding = self.get_encoding()
        return self._encoding

    def decode(self, data: bytes) -> str:
        try:
            return data.decode("ascii")
        except UnicodeDecodeError:
            return data.decode(self.encoding)

    def encode(self, data: str) -> bytes:
        try:
            return data.encode("ascii")
        except UnicodeEncodeError:
            return data.encode(self.encoding)

    def result(
        self, rc: int, cmd: bytes, stdout: Union[str, bytes], stderr: Union[str, bytes]
    ) -> CommandResult:
        result = CommandResult(
            backend=self,
            exit_status=rc,
            command=cmd,
            _stdout=stdout,
            _stderr=stderr,
        )
        logger.debug("RUN %s", result)
        return result
