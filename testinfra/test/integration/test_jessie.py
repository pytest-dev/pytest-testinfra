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

import sys

import pytest

pytestmark = pytest.mark.integration
testinfra_hosts = [
    "%s://debian_jessie" % (b_type,)
    for b_type in ("ssh", "paramiko", "safe-ssh", "docker")
]

if sys.version_info[0] == 2:
    testinfra_hosts.append("ansible://debian_jessie")


def test_ssh_package(Package):
    ssh = Package("openssh-server")
    assert ssh.is_installed
    assert ssh.version == "1:6.7p1-5"


@pytest.mark.parametrize("name,running,enabled", [
    ("ssh", True, True),
    ("ntp", False, True),
    ("salt-minion", False, False),
])
def test_service(Command, Service, name, running, enabled):

    if name == "ntp":
        # Systemd say no but sysv say yes
        assert Command("systemctl is-enabled ntp").rc == 1

    service = Service(name)
    assert service.is_running == running
    assert service.is_enabled == enabled


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


def test_encoding(testinfra_backend, Command):
    if testinfra_backend.get_connection_type() == "ansible":
        pytest.skip("ansible handle encoding himself")

    # jessie image is fr_FR@ISO-8859-15
    cmd = Command("ls -l %s", "/é")
    assert cmd.command == b"ls -l '/\xe9'"
    if testinfra_backend.get_connection_type() == "docker":
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


def test_socket(testinfra_backend, Socket):
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

    if not testinfra_backend.get_connection_type() == "docker":
        for spec in (
            "tcp://22",
            "tcp://0.0.0.0:22",
        ):
            assert len(Socket(spec).clients) >= 1
    assert not Socket("tcp://4242").is_listening


def test_ansible_module(testinfra_backend, Ansible):
    if not testinfra_backend.get_connection_type() == "ansible":
        with pytest.raises(RuntimeError) as excinfo:
            setup = Ansible("setup")
        assert (
            'Ansible module is only available with ansible '
            'connection backend') in str(excinfo.value)
    else:
        setup = Ansible("setup")["ansible_facts"]
        assert setup["ansible_lsb"]["codename"] == "jessie"
        assert Ansible("file", "path=/etc/passwd") == {
            'changed': False,
            'gid': 0,
            'group': 'root',
            'invocation': {
                'module_args': 'path=/etc/passwd',
                'module_complex_args': {},
                'module_name': 'file'
            },
            'mode': '0644',
            'owner': 'root',
            'path': '/etc/passwd',
            'size': 1369,
            'state': 'file',
            'uid': 0,
        }


def test_process(Process):
    sshd = Process("systemd")
    assert sshd.name == "systemd"
    assert sshd.user == "root"
    assert sshd.pid == "1"
    assert sshd.group == "root"
    assert float(sshd.cpu_percent) >= 0
    assert float(sshd.mem_percent) >= 0
