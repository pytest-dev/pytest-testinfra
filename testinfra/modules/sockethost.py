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

import socket

from testinfra.modules.base import Module


def parse_socketspec(socketspec):

    protocol, address = socketspec.split("://", 1)

    if protocol not in ("udp", "tcp"):
        raise RuntimeError(
            "Cannot validate protocol '%s'. Should be tcp or udp" % (
                protocol,))

    if ":" in address:
        # tcp://127.0.0.1:22
        host, port = address.rsplit(":", 1)
    else:
        # tcp://22
        host = None
        port = address

    if host is not None:
        pass
    else:
        raise RuntimeError("Hostname is missing '%s'" % (host,))

    if port is not None:
        try:
            port = int(port)
        except ValueError:
            raise RuntimeError("Cannot validate port '%s'" % (port,))

    return protocol, host, port


class SocketHost(Module):
    """Test listening tcp/udp sockets

    ``socketspec`` must be specified as ``<protocol>://<host>:<port>``

    Example:

      - All ipv4 tcp sockets on port 22: ``tcp://22``
      - All ipv4 sockets on port 22: ``tcp://0.0.0.0:22``
      - udp socket on 127.0.0.1 port 69: ``udp://127.0.0.1:69``

    """

    def __init__(self, socketspec, _attrs_cache=None):
        self._attrs_cache = _attrs_cache
        if socketspec is not None:
            self.protocol, self.host, self.port = parse_socketspec(socketspec)
        else:
            self.protocol = self.host = self.port = None

    @property
    def _attrs(self):
        self._attrs_cache = {}
        if not self._attrs_cache:
            t = socket.gethostbyname_ex(self.host)
            if t:
                self._attrs_cache['host'] = t[0]
                self._attrs_cache['aliaslist'] = t[1]
                self._attrs_cache['ipaddrlist'] = t[2]
            else:
                self._attrs_cache = {}
        return self._attrs_cache

    @property
    def is_resolvable(self):
        """Test if host is resolvable

        Translate a host name to IPv4 address format, extended interface.
        Return a triple (hostname, aliaslist, ipaddrlist) where hostname
        is the primary host name responding to the given ip_address,
        aliaslist is a (possibly empty) list of alternative host names for
        the same address, and ipaddrlist is a list of IPv4 addresses for the
        same interface on the same host (often but not always a single address)
        Does not support IPv6 name reslution.

        """
        return bool(self._attrs)

    @property
    def is_reachable(self):
        """Test if host is reachable"""
        if self.protocol == 'udp':
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif self.protocol == 'tcp':
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self._attrs:
            try:
                sock.connect((self._attrs_cache['ipaddrlist'][0], self.port))
                sock.close()
                return True
            except socket.error:
                return False
