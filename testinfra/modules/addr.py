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

from testinfra.modules.base import Module


class _AddrPort:
    def __init__(self, addr, port):
        self._addr = addr
        self._port = str(port)

    @property
    def is_reachable(self):
        """Return if port is reachable"""
        if not self._addr._host.exists("nc"):
            if self._addr.namespace:
                # in this case cannot use namespace
                raise NotImplementedError(
                    "nc command not available, namespace cannot be used"
                )
            # Fallback to bash if netcat is not available
            return (
                self._addr.run_expect(
                    [0, 1, 124],
                    "timeout 1 bash -c 'cat < /dev/null > /dev/tcp/%s/%s'",
                    self._addr.name,
                    self._port,
                ).rc
                == 0
            )

        return (
            self._addr.run(
                "{}nc -w 1 -z {} {}".format(
                    self._addr._prefix, self._addr.name, self._port
                )
            ).rc
            == 0
        )


class Addr(Module):
    """Test remote address

    Example:

    >>> google = host.addr("google.com")
    >>> google.is_resolvable
    True
    >>> '173.194.32.225' in google.ipv4_addresses
    True
    >>> google.is_reachable
    True
    >>> google.port(443).is_reachable
    True
    >>> google.port(666).is_reachable
    False

    Can also be use within a network namespace_.

    >>> localhost = host.addr("localhost", "ns1")
    >>> localhost.is_resolvable
    True

    Network namespaces can only be used if ip_ command is available
    because in this case, the module use ip-netns_ as command prefix.
    In the other case, it will raise NotImplementedError.

    .. _namespace: https://man7.org/linux/man-pages/man7/namespaces.7.html
    .. _ip: https://man7.org/linux/man-pages/man8/ip.8.html
    .. _ip-netns: https://man7.org/linux/man-pages/man8/ip-netns.8.html
    """

    def __init__(self, name, namespace=None):
        self._name = name
        self._namespace = namespace
        if self.namespace and not self._host.exists("ip"):
            raise NotImplementedError(
                "ip command not available, namespace cannot be used"
            )
        super().__init__()

    @property
    def name(self):
        """Return host name"""
        return self._name

    @property
    def namespace(self):
        """Return network namespace"""
        return self._namespace

    @property
    def _prefix(self):
        """Return the prefix to use for commands"""
        prefix = ""
        if self.namespace:
            prefix = "ip netns exec {} ".format(self.namespace)
        return prefix

    @property
    def namespace_exists(self):
        """Test if the network namespace exists"""
        # could use ip netns list instead
        return (
            self.namespace
            and self.run_test("test -e /var/run/netns/%s", self.namespace).rc == 0
        )

    @property
    def is_resolvable(self):
        """Return if address is resolvable"""
        return len(self.ip_addresses) > 0

    @property
    def is_reachable(self):
        """Return if address is reachable"""
        return (
            self.run_expect(
                [0, 1, 2], "{}ping -W 1 -c 1 {}".format(self._prefix, self.name)
            ).rc
            == 0
        )

    @property
    def ip_addresses(self):
        """Return IP addresses of host"""
        return self._resolve("ahosts")

    @property
    def ipv4_addresses(self):
        """Return IPv4 addresses of host"""
        return self._resolve("ahostsv4")

    @property
    def ipv6_addresses(self):
        """Return IPv6 addresses of host"""
        return self._resolve("ahostsv6")

    def port(self, port):
        """Return address-port pair"""
        return _AddrPort(self, port)

    def __repr__(self):
        return "<addr {}>".format(self.name)

    def _resolve(self, method):
        result = self.run_expect(
            [0, 1, 2], "{}getent {} {}".format(self._prefix, method, self.name)
        )
        lines = result.stdout.splitlines()
        return list({line.split()[0] for line in lines})
