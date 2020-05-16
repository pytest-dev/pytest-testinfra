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

import socket

from testinfra.modules.base import Module
from testinfra.utils import cached_property


def parse_socketspec(socketspec):

    protocol, address = socketspec.split("://", 1)

    if protocol not in ("udp", "tcp", "unix"):
        raise RuntimeError(
            "Cannot validate protocol '%s'. Should be tcp, udp or unix" % (
                protocol,))

    if protocol == "unix":
        # unix:///foo/bar.sock
        host = address
        port = None
    elif ":" in address:
        # tcp://127.0.0.1:22
        # tcp://:::22
        host, port = address.rsplit(":", 1)
    else:
        # tcp://22
        host = None
        port = address

    family = None
    if protocol != "unix" and host is not None:
        for f in (socket.AF_INET, socket.AF_INET6):
            try:
                socket.inet_pton(f, host)
            except socket.error:
                pass
            else:
                family = f
                break

        if family is None:
            raise RuntimeError("Cannot validate ip address '%s'" % (host,))

    if port is not None:
        try:
            port = int(port)
        except ValueError:
            raise RuntimeError("Cannot validate port '%s'" % (port,))

    return protocol, host, port


class Socket(Module):
    """Test listening tcp/udp and unix sockets

    ``socketspec`` must be specified as ``<protocol>://<host>:<port>``

    This module requires the ``netstat`` command to on the target host.

    Example:

      - Unix sockets: ``unix:///var/run/docker.sock``
      - All ipv4 and ipv6 tcp sockets on port 22: ``tcp://22``
      - All ipv4 sockets on port 22: ``tcp://0.0.0.0:22``
      - All ipv6 sockets on port 22: ``tcp://:::22``
      - udp socket on 127.0.0.1 port 69: ``udp://127.0.0.1:69``

    """
    _command = None

    def __init__(self, socketspec):
        if socketspec is not None:
            self.protocol, self.host, self.port = parse_socketspec(socketspec)
        else:
            self.protocol = self.host = self.port = None
        super().__init__()

    @property
    def is_listening(self):
        """Test if socket is listening

        >>> host.socket("unix:///var/run/docker.sock").is_listening
        False
        >>> # This HTTP server listen on all ipv4 adresses but not on ipv6
        >>> host.socket("tcp://0.0.0.0:80").is_listening
        True
        >>> host.socket("tcp://:::80").is_listening
        False
        >>> host.socket("tcp://80").is_listening
        False

        .. note:: If you don't specify a host for udp and tcp sockets,
                  then the socket is listening if and only if the
                  socket listen on **both** all ipv4 and ipv6 addresses
                  (ie 0.0.0.0 and ::)
        """
        sockets = list(self._iter_sockets(True))
        if self.protocol == "unix":
            return ("unix", self.host) in sockets
        allipv4 = (self.protocol, "0.0.0.0", self.port) in sockets
        allipv6 = (self.protocol, "::", self.port) in sockets
        return (
            any([allipv6, all([allipv4, allipv6])])
            or (
                self.host is not None
                and (
                    (":" in self.host and allipv6 in sockets)
                    or (":" not in self.host and allipv4 in sockets)
                    or (self.protocol, self.host, self.port) in sockets)
                )
        )

    @property
    def clients(self):
        """Return a list of clients connected to a listening socket

        For tcp and udp sockets a list of pair (adress, port) is returned.
        For unix sockets a list of None is returned (thus you can make a
        len() for counting clients).

        >>> host.socket("tcp://22").clients
        [('2001:db8:0:1', 44298), ('192.168.31.254', 34866)]
        >>> host.socket("unix:///var/run/docker.sock")
        [None, None, None]

        """
        sockets = []
        for sock in self._iter_sockets(False):
            if sock[0] != self.protocol:
                continue

            if self.protocol == "unix":
                if sock[1] == self.host:
                    sockets.append(None)
                continue

            if sock[2] != self.port:
                continue

            if (
                self.host is None
                or (self.host == "0.0.0.0" and ":" not in sock[3])
                or (self.host == "::" and ":" in sock[3])
                or self.host == sock[3]
            ):
                sockets.append((sock[3], sock[4]))
        return sockets

    @classmethod
    def get_listening_sockets(cls):
        """Return a list of all listening sockets

        >>> host.socket.get_listening_sockets()
        ['tcp://0.0.0.0:22', 'tcp://:::22', 'unix:///run/systemd/private', ...]
        """
        sockets = []
        for sock in cls(None)._iter_sockets(True):
            if sock[0] == "unix":
                sockets.append("unix://" + sock[1])
            else:
                sockets.append("%s://%s:%s" % (
                    sock[0], sock[1], sock[2],
                ))
        return sockets

    def _iter_sockets(self, listening):
        raise NotImplementedError

    def __repr__(self):
        return "<socket %s://%s%s>" % (
            self.protocol,
            self.host + ":" if self.host else "",
            self.port,
        )

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            for cmd, impl in (
                ('ss', LinuxSocketSS),
                ('netstat', LinuxSocketNetstat),
            ):
                try:
                    command = host.find_command(cmd)
                except ValueError:
                    pass
                else:
                    return type(impl.__name__, (impl,), {'_command': command})
            raise RuntimeError(
                'could not use the Socket module, either "ss" or "netstat"'
                ' utility is required in $PATH')
        if host.system_info.type.endswith("bsd"):
            return BSDSocket
        raise NotImplementedError


class LinuxSocketSS(Socket):

    def _iter_sockets(self, listening):
        cmd = '%s --numeric'
        if listening:
            cmd += ' --listening'
        else:
            cmd += ' --all'
        if self.protocol == 'tcp':
            cmd += ' --tcp'
        elif self.protocol == 'udp':
            cmd += ' --udp'
        elif self.protocol == 'unix':
            cmd += ' --unix'

        for line in self.run(cmd, self._command).stdout_bytes.splitlines()[1:]:
            # Ignore unix datagram sockets.
            if line.split(None, 1)[0] == b'u_dgr':
                continue
            splitted = line.decode().split()

            # If listing only TCP or UDP sockets, output has 5 columns:
            # (State, Recv-Q, Send-Q, Local Address:Port, Peer Address:Port)
            if self.protocol in ('tcp', 'udp'):
                protocol = self.protocol
                status, local, remote = (
                    splitted[0], splitted[3], splitted[4])
            # If listing all or just unix sockets, output has 6 columns:
            # Netid, State, Recv-Q, Send-Q, LocalAddress:Port, PeerAddress:Port
            else:
                protocol, status, local, remote = (
                    splitted[0], splitted[1], splitted[4], splitted[5])

            # ss reports unix socket as u_str.
            if protocol == 'u_str':
                protocol = 'unix'
                host, port = local, None
            elif protocol in ('tcp', 'udp'):
                host, port = local.rsplit(':', 1)
                port = int(port)
                # new versions of ss output ipv6 adresses enclosed in []
                if host and host[0] == '[' and host[-1] == ']':
                    host = host[1:-1]
            else:
                continue

            # UDP listening sockets may be in 'UNCONN' status.
            if listening and status in ('LISTEN', 'UNCONN'):
                if host == '*' and protocol in ('tcp', 'udp'):
                    yield protocol, '::', port
                    yield protocol, '0.0.0.0', port
                elif protocol in ('tcp', 'udp'):
                    yield protocol, host, port
                else:
                    yield protocol, host
            elif not listening and status == 'ESTAB':
                if protocol in ('tcp', 'udp'):
                    remote_host, remote_port = remote.rsplit(':', 1)
                    remote_port = int(remote_port)
                    yield protocol, host, port, remote_host, remote_port
                else:
                    yield protocol, remote


class LinuxSocketNetstat(Socket):

    def _iter_sockets(self, listening):
        cmd = "%s -n"

        if listening:
            cmd += " -l"

        if self.protocol == "tcp":
            cmd += " -t"
        elif self.protocol == "udp":
            cmd += " -u"
        elif self.protocol == "unix":
            cmd += " --unix"

        for line in self.check_output(cmd, self._command).splitlines():
            line = line.replace("\t", " ")
            splitted = line.split()
            protocol = splitted[0]
            if protocol in ("udp", "tcp", "tcp6", "udp6"):
                if protocol == "udp6":
                    protocol = "udp"
                elif protocol == "tcp6":
                    protocol = "tcp"
                address = splitted[3]
                host, port = address.rsplit(":", 1)
                port = int(port)
                if listening:
                    yield protocol, host, port
                else:
                    remote = splitted[4]
                    remote_host, remote_port = remote.rsplit(":", 1)
                    remote_port = int(remote_port)
                    yield protocol, host, port, remote_host, remote_port
            elif protocol == "unix":
                yield protocol, splitted[-1]


class BSDSocket(Socket):

    @cached_property
    def _command(self):
        return self.find_command('netstat')

    def _iter_sockets(self, listening):
        cmd = "%s -n"

        if listening:
            cmd += " -a"

        if self.protocol == "unix":
            cmd += " -f unix"

        for line in self.check_output(cmd, self._command).splitlines():
            line = line.replace("\t", " ")
            splitted = line.split()
            # FreeBSD: tcp4/tcp6
            # OpeNBSD/NetBSD: tcp/tcp6
            if splitted[0] in ("tcp", "udp", "udp4", "tcp4", "tcp6", "udp6"):

                address = splitted[3]
                if address == '*.*':
                    # On OpenBSD 6.3 (issue #338)
                    # udp          0      0  *.*                    *.*
                    # udp6         0      0  *.*                    *.*
                    continue
                host, port = address.rsplit(".", 1)
                port = int(port)

                if host == "*":
                    if splitted[0] in ("udp6", "tcp6"):
                        host = "::"
                    else:
                        host = "0.0.0.0"

                if splitted[0] in ("udp", "udp6", "udp4"):
                    protocol = "udp"
                elif splitted[0] in ("tcp", "tcp6", "tcp4"):
                    protocol = "tcp"

                remote = splitted[4]
                if remote == "*.*" and listening:
                    yield protocol, host, port
                elif not listening:
                    remote_host, remote_port = remote.rsplit(".", 1)
                    remote_port = int(remote_port)
                    yield protocol, host, port, remote_host, remote_port
            elif len(splitted) == 9 and splitted[1] in ("stream", "dgram"):
                if (
                    (splitted[4] != "0" and listening)
                    or (splitted[4] == "0" and not listening)
                ):
                    yield 'unix', splitted[-1]
