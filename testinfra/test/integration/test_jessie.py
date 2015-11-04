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

import pytest

pytestmark = pytest.mark.integration
testinfra_hosts = [
    "%s://debian_jessie" % (b_type,)
    for b_type in ("ssh", "paramiko", "safe-ssh", "docker")
]


def test_ssh_package(Package):
    ssh = Package("openssh-server")
    assert ssh.is_installed
    assert ssh.version == "1:6.7p1-5"


def test_ssh_service(Service):
    ssh = Service("ssh")
    assert ssh.is_running
    assert ssh.is_enabled


def test_service_sysv_legacy(Command, Service):
    # Systemd say no but sysv say yes
    assert Command("systemctl is-enabled ntp").rc == 1
    assert Service("ntp").is_enabled


def test_systeminfo(SystemInfo):
    assert SystemInfo.type == "linux"
    assert SystemInfo.release[:2] == "8."
    assert SystemInfo.distribution == "debian"
    assert SystemInfo.codename == "jessie"


def test_salt(Salt):
    assert Salt("pkg.version", "openssh-server", local=True) == "1:6.7p1-5"


def test_puppet_resource(PuppetResource):
    assert PuppetResource("package", "openssh-server") == {
        "openssh-server": {"ensure": "1:6.7p1-5"},
    }


def test_facter(Facter):
    assert Facter()["lsbdistcodename"] == "jessie"
    assert Facter("lsbdistcodename") == {
        "lsbdistcodename": "jessie",
    }


def test_sysctl(Sysctl):
    assert Sysctl("kernel.hostname") == "debian_jessie"
    assert isinstance(Sysctl("kernel.panic"), int)


def test_encoding(_testinfra_host, Command):
    # jessie image is fr_FR@ISO-8859-15
    cmd = Command("ls -l %s", "/é")
    assert cmd.command == b"ls -l '/\xe9'"
    if _testinfra_host.startswith("docker://"):
        # docker bug ?
        assert cmd.stderr_bytes == (
            b"ls: impossible d'acc\xe9der \xe0 /\xef\xbf\xbd: "
            b"Aucun fichier ou dossier de ce type\n"
        )
    else:
        assert cmd.stderr_bytes == (
            b"ls: impossible d'acc\xe9der \xe0 /\xe9: "
            b"Aucun fichier ou dossier de ce type\n"
        )
        assert cmd.stderr == (
            "ls: impossible d'accéder à /é: "
            "Aucun fichier ou dossier de ce type\n"
        )


def test_socket(_testinfra_host, Socket):
    listening = Socket.get_listening_sockets()
    for spec in (
        "tcp://0.0.0.0:22",
        "tcp://:::22",
        "unix:///run/systemd/private",
    ):
        assert spec in listening
    for spec in (
        "tcp://22",
        "tcp://0.0.0.0:22",
        "tcp://127.0.0.1:22",
        "tcp://:::22",
        "tcp://::1:22",
    ):
        socket = Socket(spec)
        assert socket.is_listening

    if not _testinfra_host.startswith("docker://"):
        for spec in (
            "tcp://22",
            "tcp://0.0.0.0:22",
        ):
            assert len(Socket(spec).clients) >= 1
    assert not Socket("tcp://4242").is_listening
