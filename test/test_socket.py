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

import errno
import shutil
import socket
import sys
from types import SimpleNamespace

import pytest

import testinfra
from testinfra.modules.socket import LinuxSocketSS


@pytest.mark.parametrize("protocol", ["tcp", "udp"])
@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("[::]", (False, False, True, True, False)),
        ("0.0.0.0", (True, True, False, False, False)),
        ("*", (True, True, True, True, True)),
        ("127.0.0.1", (False, True, False, False, False)),
        ("[::1]", (False, False, False, True, False)),
    ],
)
def test_ss_listening_address_family(monkeypatch, protocol, address, expected):
    status = "LISTEN" if protocol == "tcp" else "UNCONN"
    output = (
        "State Recv-Q Send-Q Local Address:Port Peer Address:Port\n"
        f"{status} 0 0 {address}:18201 *:*\n"
    ).encode()
    monkeypatch.setattr(
        LinuxSocketSS, "run", lambda *args: SimpleNamespace(stdout_bytes=output)
    )
    hosts = ("0.0.0.0", "127.0.0.1", "::", "::1", None)
    for host, result in zip(hosts, expected, strict=True):
        address_spec = "" if host is None else host + ":"
        sock = LinuxSocketSS(f"{protocol}://{address_spec}18201")
        assert sock.is_listening is result
        # Wildcards on other ports must not affect this result.
        assert not LinuxSocketSS(f"{protocol}://{address_spec}18202").is_listening


@pytest.mark.parametrize("protocol", ["tcp", "udp"])
def test_ss_two_wildcards_satisfy_hostless(monkeypatch, protocol):
    status = "LISTEN" if protocol == "tcp" else "UNCONN"
    output = (
        "State Recv-Q Send-Q Local Address:Port Peer Address:Port\n"
        f"{status} 0 0 0.0.0.0:18201 *:*\n"
        f"{status} 0 0 [::]:18201 *:*\n"
    ).encode()
    monkeypatch.setattr(
        LinuxSocketSS, "run", lambda *args: SimpleNamespace(stdout_bytes=output)
    )
    assert LinuxSocketSS(f"{protocol}://18201").is_listening


def test_ss_unix_listening(monkeypatch):
    output = (
        b"Netid State Recv-Q Send-Q Local Address:Port Peer Address:Port\n"
        b"u_str LISTEN 0 128 /tmp/testinfra.sock 42 * 0\n"
    )
    monkeypatch.setattr(
        LinuxSocketSS, "run", lambda *args: SimpleNamespace(stdout_bytes=output)
    )
    assert LinuxSocketSS("unix:///tmp/testinfra.sock").is_listening
    assert not LinuxSocketSS("unix:///tmp/missing.sock").is_listening


@pytest.mark.skipif(
    sys.platform != "linux" or not shutil.which("ss"), reason="requires Linux ss"
)
@pytest.mark.parametrize("v6only", [True, False])
def test_ss_tcp_ipv6_wildcard_local(v6only):
    if not socket.has_ipv6:
        pytest.skip("IPv6 is unavailable")
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, v6only)
        try:
            server.bind(("::", 0))
        except OSError as exc:
            if exc.errno in (errno.EADDRNOTAVAIL, errno.EAFNOSUPPORT):
                pytest.skip("IPv6 loopback is unavailable")
            raise
        server.listen(1)
        port = server.getsockname()[1]
        local_host = testinfra.get_host("local://")
        assert isinstance(local_host.socket(f"tcp://{port}"), LinuxSocketSS)
        assert local_host.socket(f"tcp://0.0.0.0:{port}").is_listening is (not v6only)
        assert local_host.socket(f"tcp://127.0.0.1:{port}").is_listening is (not v6only)
        assert local_host.socket(f"tcp://{port}").is_listening is (not v6only)
        assert local_host.socket(f"tcp://:::{port}").is_listening
        assert local_host.socket(f"tcp://::1:{port}").is_listening
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(1)
            result = client.connect_ex(("127.0.0.1", port))
            assert result == (errno.ECONNREFUSED if v6only else 0)
