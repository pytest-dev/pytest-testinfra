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

import os
import socket


def test_udp_socket_listening(host):
    # Set-up a listening socket.
    address = "127.0.0.1"
    port = 10000
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((address, port))

    # Set-up the testinfra socket for testing.
    test_socket_spec = "udp://%s:%d" % (address, port)
    test_socket = host.socket(test_socket_spec)

    assert test_socket.is_listening


def test_udp_socket_not_listening(host):
    address = "127.0.0.1"
    port = 10001

    test_socket_spec = "udp://%s:%d" % (address, port)
    test_socket = host.socket(test_socket_spec)

    assert not test_socket.is_listening


def test_tcp_socket_listening(host):
    # Set-up a listening socket.
    address = "127.0.0.1"
    port = 10000
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((address, port))
    tcp_socket.listen(1)

    # Set-up the testinfra socket for testing.
    test_socket_spec = "tcp://%s:%d" % (address, port)
    test_socket = host.socket(test_socket_spec)

    assert test_socket.is_listening


def test_tcp_socket_not_listening(host):
    address = "127.0.0.1"
    port = 10001

    test_socket_spec = "tcp://%s:%d" % (address, port)
    test_socket = host.socket(test_socket_spec)

    assert not test_socket.is_listening


def test_unix_socket_listening(host):
    # Set-up a listening socket.
    address = '/tmp/mytestsocket'

    # Make sure the socket does not already exist
    try:
        os.unlink(address)
    except OSError:
        if os.path.exists(address):
            raise Exception('Socket path could not be unlinked: %s' % address)

    unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    unix_socket.bind(address)
    unix_socket.listen(1)

    # Set-up the testinfra socket for testing.
    test_socket_spec = "unix://%s" % address
    test_socket = host.socket(test_socket_spec)

    assert test_socket.is_listening


def test_unix_socket_not_listening(host):
    address = '/tmp/mytestsocketdoesnotexist'

    # Set-up the testinfra socket for testing.
    test_socket_spec = "unix://%s" % address
    test_socket = host.socket(test_socket_spec)

    assert not test_socket.is_listening
