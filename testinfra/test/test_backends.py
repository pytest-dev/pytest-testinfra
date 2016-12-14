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
import pytest
import six

import testinfra.backend
BACKENDS = ("ssh", "safe-ssh", "docker", "paramiko", "ansible")
HOSTS = [backend + "://debian_jessie" for backend in BACKENDS]
USER_HOSTS = [backend + "://user@debian_jessie" for backend in BACKENDS]
SUDO_HOSTS = [
    backend + "://user@debian_jessie?sudo=True"
    for backend in BACKENDS
]
SUDO_USER_HOSTS = [
    backend + "://debian_jessie?sudo=True&sudo_user=user"
    for backend in BACKENDS
]


@pytest.mark.testinfra_hosts(*(
    HOSTS + USER_HOSTS + SUDO_HOSTS + SUDO_USER_HOSTS))
def test_command(Command):
    assert Command.check_output("true") == ""
    # test that quotting is correct
    assert Command("echo a b | grep -q %s", "a c").rc == 1


@pytest.mark.testinfra_hosts(*HOSTS)
def test_encoding(TestinfraBackend, Command):
    if TestinfraBackend.get_connection_type() == "ansible":
        pytest.skip("ansible handle encoding himself")

    # jessie image is fr_FR@ISO-8859-15
    cmd = Command("ls -l %s", "/é")
    if TestinfraBackend.get_connection_type() == "docker":
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


@pytest.mark.testinfra_hosts(*(USER_HOSTS + SUDO_USER_HOSTS))
def test_user_connection(User):
    assert User().name == "user"


@pytest.mark.testinfra_hosts(*SUDO_HOSTS)
def test_sudo(User):
    assert User().name == "root"


@pytest.mark.testinfra_hosts("ansible://debian_jessie")
def test_ansible_hosts_expand(TestinfraBackend):
    from testinfra.backend.ansible import AnsibleBackend

    def get_hosts(spec):
        return AnsibleBackend.get_hosts(
            spec, ansible_inventory=TestinfraBackend.ansible_inventory)
    assert get_hosts(["all"]) == ["debian_jessie"]
    assert get_hosts(["testgroup"]) == ["debian_jessie"]
    assert get_hosts(["*ia*jess*"]) == ["debian_jessie"]


def test_backend_importables():
    # just check that all declared backend are importable and NAME is set
    # correctly
    for connection_type in testinfra.backend.BACKENDS:
        if six.PY3 and connection_type == 'ansible':
            pytest.skip()
        obj = testinfra.backend.get_backend_class(connection_type)
        assert obj.get_connection_type() == connection_type
