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

import testinfra.backend
from testinfra.backend.base import BaseBackend
from testinfra.backend.base import HostSpec
from testinfra.backend.winrm import _quote
BACKENDS = ("ssh", "safe-ssh", "docker", "paramiko", "ansible")
HOSTS = [backend + "://debian_stretch" for backend in BACKENDS]
USER_HOSTS = [backend + "://user@debian_stretch" for backend in BACKENDS]
SUDO_HOSTS = [
    backend + "://user@debian_stretch?sudo=True"
    for backend in BACKENDS
]
SUDO_USER_HOSTS = [
    backend + "://debian_stretch?sudo=True&sudo_user=user"
    for backend in BACKENDS
]


@pytest.mark.testinfra_hosts(*(
    HOSTS + USER_HOSTS + SUDO_HOSTS + SUDO_USER_HOSTS))
def test_command(host):
    assert host.check_output("true") == ""
    # test that quotting is correct
    assert host.run("echo a b | grep -q %s", "a c").rc == 1


@pytest.mark.testinfra_hosts(*HOSTS)
def test_encoding(host):
    if host.backend.get_connection_type() == "ansible":
        pytest.skip("ansible handle encoding himself")

    # stretch image is fr_FR@ISO-8859-15
    cmd = host.run("ls -l %s", "/é")
    if host.backend.get_connection_type() == "docker":
        # docker bug ?
        assert cmd.stderr_bytes == (
            b"ls: impossible d'acc\xe9der \xe0 '/\xef\xbf\xbd': "
            b"Aucun fichier ou dossier de ce type\n"
        )
    else:
        assert cmd.stderr_bytes == (
            b"ls: impossible d'acc\xe9der \xe0 '/\xe9': "
            b"Aucun fichier ou dossier de ce type\n"
        )
        assert cmd.stderr == (
            "ls: impossible d'accéder à '/é': "
            "Aucun fichier ou dossier de ce type\n"
        )


@pytest.mark.testinfra_hosts(*(USER_HOSTS + SUDO_USER_HOSTS))
def test_user_connection(host):
    assert host.user().name == "user"


@pytest.mark.testinfra_hosts(*SUDO_HOSTS)
def test_sudo(host):
    assert host.user().name == "root"


@pytest.mark.testinfra_hosts("ansible://debian_stretch")
def test_ansible_hosts_expand(host):
    from testinfra.backend.ansible import AnsibleBackend

    def get_hosts(spec):
        return AnsibleBackend.get_hosts(
            spec, ansible_inventory=host.backend.ansible_inventory)
    assert get_hosts(["all"]) == ["debian_stretch"]
    assert get_hosts(["testgroup"]) == ["debian_stretch"]
    assert get_hosts(["*ia*stre*"]) == ["debian_stretch"]


def test_backend_importables():
    # just check that all declared backend are importable and NAME is set
    # correctly
    for connection_type in testinfra.backend.BACKENDS:
        obj = testinfra.backend.get_backend_class(connection_type)
        assert obj.get_connection_type() == connection_type


@pytest.mark.testinfra_hosts("docker://centos_7", "ssh://centos_7")
def test_docker_encoding(host):
    encoding = host.check_output(
        "python -c 'import locale;print(locale.getpreferredencoding())'")
    assert encoding == "ANSI_X3.4-1968"
    string = "ťēꞩƫìṇḟřặ ṧꝕèȃǩ ửƫᵮ8"
    assert host.check_output("echo %s | tee /tmp/s.txt", string) == string
    assert host.file("/tmp/s.txt").content_string.strip() == string


@pytest.mark.parametrize('hostspec,expected', [
    ('u:P@h:p', HostSpec('h', 'p', 'u', 'P')),
    ('u@h:p', HostSpec('h', 'p', 'u', None)),
    ('u:P@h', HostSpec('h', None, 'u', 'P')),
    ('u@h', HostSpec('h', None, 'u', None)),
    ('h', HostSpec('h', None, None, None)),
])
def test_parse_hostspec(hostspec, expected):
    assert BaseBackend.parse_hostspec(hostspec) == expected


@pytest.mark.parametrize('hostspec,pod,container,namespace', [
    ('kubectl://pod', 'pod', None, None),
    ('kubectl://pod?namespace=n', 'pod', None, 'n'),
    ('kubectl://pod?container=c&namespace=n', 'pod', 'c', 'n'),
])
def test_kubectl_hostspec(hostspec, pod, container, namespace):
    backend = testinfra.get_host(hostspec).backend
    assert backend.name == pod
    assert backend.container == container
    assert backend.namespace == namespace


@pytest.mark.parametrize('arg_string,expected', [
    (
        'C:\\Users\\vagrant\\This Dir\\salt',
        '"C:\\Users\\vagrant\\This Dir\\salt"'
    ),
    (
        'C:\\Users\\vagrant\\AppData\\Local\\Temp\\kitchen\\etc\\salt',
        '"C:\\Users\\vagrant\\AppData\\Local\\Temp\\kitchen\\etc\\salt"'
    ),
])
def test_winrm_quote(arg_string, expected):
    assert _quote(arg_string) == expected
