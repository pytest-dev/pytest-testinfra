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

import operator
import os
import pytest
import tempfile

import testinfra
import testinfra.backend
from testinfra.backend.base import BaseBackend
from testinfra.backend.base import HostSpec
from testinfra.backend.winrm import _quote
from testinfra.utils.ansible_runner import AnsibleRunner
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


def test_ansible_get_hosts():
    with tempfile.NamedTemporaryFile() as f:
        f.write((
            b'ungrp\n'
            b'[g1]\n'
            b'debian\n'
            b'[g2]\n'
            b'centos\n'
            b'[g3:children]\n'
            b'g1\n'
            b'g2\n'
            b'[g4:children]\n'
            b'g3'
        ))
        f.flush()

        def get_hosts(spec):
            return AnsibleRunner(f.name).get_hosts(spec)
        assert get_hosts("all") == ["centos", "debian", "ungrp"]
        assert get_hosts("*") == ["centos", "debian", "ungrp"]
        assert get_hosts("g1") == ["debian"]
        assert get_hosts("*2") == ["centos"]
        assert get_hosts("*ia*") == ["debian"]
        assert get_hosts('*3') == ["centos", "debian"]
        assert get_hosts('*4') == ["centos", "debian"]
        assert get_hosts('ungrouped') == ["ungrp"]
        assert get_hosts('un*') == ["ungrp"]
        assert get_hosts('nope') == []


def test_ansible_get_variables():
    with tempfile.NamedTemporaryFile() as f:
        f.write((
            b'debian a=b c=d\n'
            b'centos e=f\n'
            b'[all:vars]\n'
            b'a=a\n'
            b'[g]\n'
            b'debian\n'
            b'[g:vars]\n'
            b'x=z\n'
        ))
        f.flush()

        def get_vars(host):
            return AnsibleRunner(f.name).get_variables(host)
        groups = {
            'all': ['centos', 'debian'],
            'g': ['debian'],
            'ungrouped': ['centos'],
        }
        assert get_vars("debian") == {
            'a': 'b',
            'c': 'd',
            'x': 'z',
            'inventory_hostname': 'debian',
            'group_names': ['g'],
            'groups': groups,
        }
        assert get_vars("centos") == {
            'a': 'a',
            'e': 'f',
            'inventory_hostname': 'centos',
            'group_names': ['ungrouped'],
            'groups': groups,
        }


@pytest.mark.parametrize('hostname,kwargs,inventory,expected', [
    ('host', {}, b'host ansible_connection=local ansible_become=yes ansible_become_user=u', {  # noqa
        'NAME': 'local',
        'sudo': True,
        'sudo_user': 'u',
    }),
    ('host', {}, b'host', {
        'NAME': 'paramiko',
        'host.name': 'host',
    }),
    ('host', {}, b'host ansible_host=127.0.1.1 ansible_user=u ansible_ssh_private_key_file=key ansible_port=2222 ansible_become=yes ansible_become_user=u', {  # noqa
        'NAME': 'paramiko',
        'sudo': True,
        'sudo_user': 'u',
        'host.name': '127.0.1.1',
        'host.port': '2222',
        'ssh_identity_file': 'key',
    }),
    ('host', {}, b'host ansible_connection=docker', {
        'NAME': 'docker',
        'name': 'host',
        'user': None,
    }),
    ('host', {}, b'host ansible_connection=docker ansible_become=yes ansible_become_user=u ansible_user=z ansible_host=container', {  # noqa
        'NAME': 'docker',
        'name': 'container',
        'user': 'z',
        'sudo': True,
        'sudo_user': 'u',
    }),
    ('host', {'ssh_config': '/ssh_config', 'ssh_identity_file': '/id_ed25519'},
        b'host', {
        'NAME': 'paramiko',
        'host.name': 'host',
        'ssh_config': '/ssh_config',
        'ssh_identity_file': '/id_ed25519',
    }),
])
def test_ansible_get_host(hostname, kwargs, inventory, expected):
    with tempfile.NamedTemporaryFile() as f:
        f.write(inventory + b'\n')
        f.flush()
        backend = AnsibleRunner(f.name).get_host(hostname, **kwargs).backend
        for attr, value in expected.items():
            assert operator.attrgetter(attr)(backend) == value


def test_ansible_no_host():
    with tempfile.NamedTemporaryFile() as f:
        f.write(b'host\n')
        f.flush()
        assert AnsibleRunner(f.name).get_hosts() == ['host']
        hosts = testinfra.get_hosts(
            [None], connection='ansible', ansible_inventory=f.name)
        assert [h.backend.get_pytest_id() for h in hosts] == ['ansible://host']
    with tempfile.NamedTemporaryFile() as f:
        # empty or no inventory should not return any hosts except for
        # localhost
        assert AnsibleRunner(f.name).get_hosts() == []
        assert AnsibleRunner(f.name).get_hosts('local*') == []
        assert AnsibleRunner(f.name).get_hosts('localhost') == ['localhost']


def test_ansible_unhandled_connection():
    with tempfile.NamedTemporaryFile() as f:
        f.write(b'host ansible_connection=winrm\n')
        f.flush()
        with pytest.raises(RuntimeError) as excinfo:
            AnsibleRunner(f.name).get_host('host')
        assert str(excinfo.value) == 'unhandled ansible_connection winrm'


def test_ansible_config():
    # test testinfra use ANSIBLE_CONFIG
    tmp = tempfile.NamedTemporaryFile
    with tmp(suffix='.cfg') as cfg, tmp() as inventory:
        cfg.write((
            b'[defaults]\n'
            b'inventory=' + inventory.name.encode() + b'\n'
        ))
        cfg.flush()
        inventory.write(b'h\n')
        inventory.flush()
        old = os.environ.get('ANSIBLE_CONFIG')
        os.environ['ANSIBLE_CONFIG'] = cfg.name
        try:
            assert AnsibleRunner(None).get_hosts('all') == ['h']
        finally:
            if old is not None:
                os.environ['ANSIBLE_CONFIG'] = old
            else:
                del os.environ['ANSIBLE_CONFIG']


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
    ('pr%C3%A9nom@h', HostSpec('h', None, 'prénom', None)),
    ('pr%C3%A9nom:p%40ss%3Aw0rd@h', HostSpec('h', None, 'prénom',
                                             'p@ss:w0rd')),
    # ipv6 matching
    ('[2001:db8:a0b:12f0::1]',
     HostSpec('2001:db8:a0b:12f0::1', None, None, None)),
    ('user:password@[2001:db8:a0b:12f0::1]',
     HostSpec('2001:db8:a0b:12f0::1', None, 'user', 'password')),
    ('user:password@[2001:4800:7819:103:be76:4eff:fe04:9229]:22',
     HostSpec('2001:4800:7819:103:be76:4eff:fe04:9229', '22',
              'user', 'password')),
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
