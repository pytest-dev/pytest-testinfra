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

HOSTS = [
    "ssh://debian_buster",
    "safe-ssh://debian_buster",
    "docker://debian_buster",
    "paramiko://debian_buster",
    "ansible://debian_buster",
    "ansible://debian_buster?force_ansible=True",
]
USER_HOSTS = [
    "ssh://user@debian_buster",
    "safe-ssh://user@debian_buster",
    "docker://user@debian_buster",
    "paramiko://user@debian_buster",
    "ansible://user@debian_buster",
    "ansible://user@debian_buster?force_ansible=True",
]
SUDO_HOSTS = [
    "ssh://user@debian_buster?sudo=True",
    "safe-ssh://user@debian_buster?sudo=True",
    "docker://user@debian_buster?sudo=True",
    "paramiko://user@debian_buster?sudo=True",
    "ansible://user@debian_buster?sudo=True",
    "ansible://user@debian_buster?force_ansible=True&sudo=True",
]
SUDO_USER_HOSTS = [
    "ssh://debian_buster?sudo=True&sudo_user=user",
    "safe-ssh://debian_buster?sudo=True&sudo_user=user",
    "docker://debian_buster?sudo=True&sudo_user=user",
    "paramiko://debian_buster?sudo=True&sudo_user=user",
    "ansible://debian_buster?sudo=True&sudo_user=user",
    "ansible://debian_buster?force_ansible=True&sudo=True&sudo_user=user",
]


@pytest.mark.testinfra_hosts(*(HOSTS + USER_HOSTS + SUDO_HOSTS + SUDO_USER_HOSTS))
def test_command(host):
    assert host.check_output("true") == ""
    # test that quotting is correct
    assert host.run("echo a b | grep -q %s", "a c").rc == 1
    out = host.run("echo out && echo err >&2 && exit 42")
    assert out.rc == 42
    if host.backend.get_connection_type() == "ansible" and host.backend.force_ansible:
        assert out.stdout_bytes == b"out"
        assert out.stderr_bytes == b"err"
    else:
        assert out.stdout_bytes == b"out\n"
        assert out.stderr_bytes == b"err\n"
    out = host.run("commandthatdoesnotexists")
    assert out.rc == 127


@pytest.mark.testinfra_hosts(*HOSTS)
def test_encoding(host):
    # buster image is fr_FR@ISO-8859-15
    cmd = host.run("ls -l %s", "/é")
    if host.backend.get_connection_type() == "docker":
        # docker bug ?
        assert cmd.stderr_bytes == (
            b"ls: impossible d'acc\xe9der \xe0 '/\xef\xbf\xbd': "
            b"Aucun fichier ou dossier de ce type\n"
        )
    elif host.backend.get_connection_type() == "ansible" and host.backend.force_ansible:
        # XXX: this encoding issue comes directly from ansible
        # not sure how to handle this...
        assert cmd.stderr == (
            "ls: impossible d'accéder à '/Ã©': " "Aucun fichier ou dossier de ce type"
        )
    else:
        assert cmd.stderr_bytes == (
            b"ls: impossible d'acc\xe9der \xe0 '/\xe9': "
            b"Aucun fichier ou dossier de ce type\n"
        )
        assert cmd.stderr == (
            "ls: impossible d'accéder à '/é': " "Aucun fichier ou dossier de ce type\n"
        )


@pytest.mark.testinfra_hosts("ansible://debian_buster?force_ansible=True")
def test_ansible_any_error_fatal(host):
    os.environ["ANSIBLE_ANY_ERRORS_FATAL"] = "True"
    try:
        out = host.run("echo out && echo err >&2 && exit 42")
        assert out.rc == 42
        assert out.stdout == "out"
        assert out.stderr == "err"
    finally:
        del os.environ["ANSIBLE_ANY_ERRORS_FATAL"]


@pytest.mark.testinfra_hosts(*(USER_HOSTS + SUDO_USER_HOSTS))
def test_user_connection(host):
    assert host.user().name == "user"


@pytest.mark.testinfra_hosts(*SUDO_HOSTS)
def test_sudo(host):
    assert host.user().name == "root"


def test_ansible_get_hosts():
    with tempfile.NamedTemporaryFile() as f:
        f.write(
            (
                b"ungrp\n"
                b"[g1]\n"
                b"debian\n"
                b"[g2]\n"
                b"centos\n"
                b"[g3:children]\n"
                b"g1\n"
                b"g2\n"
                b"[g4:children]\n"
                b"g3"
            )
        )
        f.flush()

        def get_hosts(spec):
            return AnsibleRunner(f.name).get_hosts(spec)

        assert get_hosts("all") == ["centos", "debian", "ungrp"]
        assert get_hosts("*") == ["centos", "debian", "ungrp"]
        assert get_hosts("g1") == ["debian"]
        assert get_hosts("*2") == ["centos"]
        assert get_hosts("*ia*") == ["debian"]
        assert get_hosts("*3") == ["centos", "debian"]
        assert get_hosts("*4") == ["centos", "debian"]
        assert get_hosts("ungrouped") == ["ungrp"]
        assert get_hosts("un*") == ["ungrp"]
        assert get_hosts("nope") == []


def test_ansible_get_variables():
    with tempfile.NamedTemporaryFile() as f:
        f.write(
            (
                b"debian a=b c=d\n"
                b"centos e=f\n"
                b"[all:vars]\n"
                b"a=a\n"
                b"[g]\n"
                b"debian\n"
                b"[g:vars]\n"
                b"x=z\n"
            )
        )
        f.flush()

        def get_vars(host):
            return AnsibleRunner(f.name).get_variables(host)

        groups = {
            "all": ["centos", "debian"],
            "g": ["debian"],
            "ungrouped": ["centos"],
        }
        assert get_vars("debian") == {
            "a": "b",
            "c": "d",
            "x": "z",
            "inventory_hostname": "debian",
            "group_names": ["g"],
            "groups": groups,
        }
        assert get_vars("centos") == {
            "a": "a",
            "e": "f",
            "inventory_hostname": "centos",
            "group_names": ["ungrouped"],
            "groups": groups,
        }


@pytest.mark.parametrize(
    "kwargs,inventory,expected",
    [
        (
            {},
            b"host ansible_connection=local ansible_become=yes ansible_become_user=u",
            {  # noqa
                "NAME": "local",
                "sudo": True,
                "sudo_user": "u",
            },
        ),
        (
            {},
            b"host",
            {
                "NAME": "ssh",
                "host.name": "host",
            },
        ),
        (
            {},
            b"host ansible_connection=smart",
            {
                "NAME": "ssh",
                "host.name": "host",
            },
        ),
        (
            {},
            b"host ansible_host=127.0.1.1 ansible_user=u ansible_ssh_private_key_file=key ansible_port=2222 ansible_become=yes ansible_become_user=u",
            {  # noqa
                "NAME": "ssh",
                "sudo": True,
                "sudo_user": "u",
                "host.name": "127.0.1.1",
                "host.port": "2222",
                "ssh_identity_file": "key",
            },
        ),
        (
            {},
            b"host ansible_host=127.0.1.1 ansible_user=u ansible_private_key_file=key ansible_port=2222 ansible_become=yes ansible_become_user=u",
            {  # noqa
                "NAME": "ssh",
                "sudo": True,
                "sudo_user": "u",
                "host.name": "127.0.1.1",
                "host.port": "2222",
                "ssh_identity_file": "key",
            },
        ),
        (
            {},
            b'host ansible_ssh_common_args="-o LogLevel=FATAL"',
            {
                "NAME": "ssh",
                "host.name": "host",
                "ssh_extra_args": "-o LogLevel=FATAL",
            },
        ),
        (
            {},
            b'host ansible_ssh_extra_args="-o LogLevel=FATAL"',
            {
                "NAME": "ssh",
                "host.name": "host",
                "ssh_extra_args": "-o LogLevel=FATAL",
            },
        ),
        (
            {},
            b'host ansible_ssh_common_args="-o StrictHostKeyChecking=no" ansible_ssh_extra_args="-o LogLevel=FATAL"',
            {  # noqa
                "NAME": "ssh",
                "host.name": "host",
                "ssh_extra_args": "-o StrictHostKeyChecking=no -o LogLevel=FATAL",
            },
        ),
        (
            {},
            b"host ansible_connection=docker",
            {
                "NAME": "docker",
                "name": "host",
                "user": None,
            },
        ),
        (
            {},
            b"host ansible_connection=docker ansible_become=yes ansible_become_user=u ansible_user=z ansible_host=container",
            {  # noqa
                "NAME": "docker",
                "name": "container",
                "user": "z",
                "sudo": True,
                "sudo_user": "u",
            },
        ),
        (
            {"ssh_config": "/ssh_config", "ssh_identity_file": "/id_ed25519"},
            b"host",
            {
                "NAME": "ssh",
                "host.name": "host",
                "ssh_config": "/ssh_config",
                "ssh_identity_file": "/id_ed25519",
            },
        ),
    ],
)
def test_ansible_get_host(kwargs, inventory, expected):
    with tempfile.NamedTemporaryFile() as f:
        f.write(inventory + b"\n")
        f.flush()
        backend = AnsibleRunner(f.name).get_host("host", **kwargs).backend
        for attr, value in expected.items():
            assert operator.attrgetter(attr)(backend) == value


@pytest.mark.parametrize(
    "inventory,expected",
    [
        (
            b"host",
            (
                "ssh -o ConnectTimeout=10 -o ControlMaster=auto "
                "-o ControlPersist=60s host true"
            ),
        ),
        # password passing from inventory: user is required
        (
            b"host ansible_user=user ansible_ssh_pass=password",
            (
                "sshpass -p password ssh -o User=user "
                "-o ConnectTimeout=10 -o ControlMaster=auto "
                "-o ControlPersist=60s host true"
            ),
        ),
        # identity_file has highest priority
        (
            b"host ansible_user=user ansible_ssh_pass=password ansible_ssh_private_key_file=some_file",
            (  # noqa
                "ssh -o User=user -i some_file "
                "-o ConnectTimeout=10 -o ControlMaster=auto "
                "-o ControlPersist=60s host true"
            ),
        ),
        # password without usr won't work
        (
            b"host ansible_ssh_pass=password",
            (
                "ssh -o ConnectTimeout=10 -o ControlMaster=auto "
                "-o ControlPersist=60s host true"
            ),
        ),
        # avoid interference between our ssh backend and ansible_ssh_extra_args
        (
            b'host ansible_ssh_extra_args="-o ConnectTimeout=5 -o ControlMaster=auto '
            b'-o ControlPersist=10s"',
            (
                "ssh -o ConnectTimeout=5 -o ControlMaster=auto -o "
                "ControlPersist=10s host true"
            ),
        ),
        # escape %
        (
            b'host ansible_ssh_extra_args="-o ControlPath ~/.ssh/ansible/cp/%r@%h-%p"',
            (  # noqa
                "ssh -o ControlPath ~/.ssh/ansible/cp/%r@%h-%p -o ConnectTimeout=10 "
                "-o ControlMaster=auto -o ControlPersist=60s host true"
            ),
        ),
    ],
)
def test_ansible_ssh_command(inventory, expected):
    with tempfile.NamedTemporaryFile() as f:
        f.write(inventory + b"\n")
        f.flush()
        backend = AnsibleRunner(f.name).get_host("host").backend
        cmd, cmd_args = backend._build_ssh_command("true")
        command = backend.quote(" ".join(cmd), *cmd_args)
        assert command == expected


def test_ansible_no_host():
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"host\n")
        f.flush()
        assert AnsibleRunner(f.name).get_hosts() == ["host"]
        hosts = testinfra.get_hosts(
            [None], connection="ansible", ansible_inventory=f.name
        )
        assert [h.backend.get_pytest_id() for h in hosts] == ["ansible://host"]
    with tempfile.NamedTemporaryFile() as f:
        # empty or no inventory should not return any hosts except for
        # localhost
        nohost = (
            "No inventory was parsed (missing file ?), "
            "only implicit localhost is available"
        )
        with pytest.raises(RuntimeError) as exc:
            assert AnsibleRunner(f.name).get_hosts() == []
        assert str(exc.value) == nohost
        with pytest.raises(RuntimeError) as exc:
            assert AnsibleRunner(f.name).get_hosts("local*") == []
        assert str(exc.value) == nohost
        assert AnsibleRunner(f.name).get_hosts("localhost") == ["localhost"]


def test_ansible_config():
    # test testinfra use ANSIBLE_CONFIG
    tmp = tempfile.NamedTemporaryFile
    with tmp(suffix=".cfg") as cfg, tmp() as inventory:
        cfg.write((b"[defaults]\n" b"inventory=" + inventory.name.encode() + b"\n"))
        cfg.flush()
        inventory.write(b"h\n")
        inventory.flush()
        old = os.environ.get("ANSIBLE_CONFIG")
        os.environ["ANSIBLE_CONFIG"] = cfg.name
        try:
            assert AnsibleRunner(None).get_hosts("all") == ["h"]
        finally:
            if old is not None:
                os.environ["ANSIBLE_CONFIG"] = old
            else:
                del os.environ["ANSIBLE_CONFIG"]


@pytest.mark.parametrize(
    "options,expected_cli,expected_args",
    [
        ({}, "--check", []),
        ({"become": True}, "--become --check", []),
        ({"check": False}, "", []),
        ({"diff": True, "check": False}, "--diff", []),
        ({"one_line": True, "check": False}, "--one-line", []),
        (
            {"become_method": "sudo", "check": False},
            "--become-method %s",
            ["sudo"],
        ),
        (
            {"become_user": "root", "check": False},
            "--become-user %s",
            ["root"],
        ),
        ({"user": "root", "check": False}, "--user %s", ["root"]),
        (
            {"extra_vars": {"target": "production", "foo": 42}, "check": False},
            "--extra-vars %s",
            ['{"target": "production", "foo": 42}'],
        ),
        ({"verbose": 0, "check": False}, "", []),
        ({"verbose": 1, "check": False}, "-v", []),
        ({"verbose": 2, "check": False}, "-vv", []),
        ({"verbose": 3, "check": False}, "-vvv", []),
        ({"verbose": 4, "check": False}, "-vvvv", []),
    ],
)
def test_ansible_options(options, expected_cli, expected_args):
    runner = AnsibleRunner()
    cli, args = runner.options_to_cli(options)
    assert cli == expected_cli
    assert args == expected_args


def test_ansible_unknown_option():
    runner = AnsibleRunner()
    with pytest.raises(KeyError, match="^'unknown'$"):
        runner.options_to_cli({"unknown": True})


def test_backend_importables():
    # just check that all declared backend are importable and NAME is set
    # correctly
    for connection_type in testinfra.backend.BACKENDS:
        obj = testinfra.backend.get_backend_class(connection_type)
        assert obj.get_connection_type() == connection_type


@pytest.mark.testinfra_hosts("docker://centos_7", "ssh://centos_7")
def test_docker_encoding(host):
    encoding = host.check_output(
        "python -c 'import locale;print(locale.getpreferredencoding())'"
    )
    assert encoding == "ANSI_X3.4-1968"
    string = "ťēꞩƫìṇḟřặ ṧꝕèȃǩ ửƫᵮ8"
    assert host.check_output("echo %s | tee /tmp/s.txt", string) == string
    assert host.file("/tmp/s.txt").content_string.strip() == string


@pytest.mark.parametrize(
    "hostspec,expected",
    [
        ("u:P@h:p", HostSpec("h", "p", "u", "P")),
        ("u@h:p", HostSpec("h", "p", "u", None)),
        ("u:P@h", HostSpec("h", None, "u", "P")),
        ("u@h", HostSpec("h", None, "u", None)),
        ("h", HostSpec("h", None, None, None)),
        ("pr%C3%A9nom@h", HostSpec("h", None, "prénom", None)),
        ("pr%C3%A9nom:p%40ss%3Aw0rd@h", HostSpec("h", None, "prénom", "p@ss:w0rd")),
        # ipv6 matching
        ("[2001:db8:a0b:12f0::1]", HostSpec("2001:db8:a0b:12f0::1", None, None, None)),
        (
            "user:password@[2001:db8:a0b:12f0::1]",
            HostSpec("2001:db8:a0b:12f0::1", None, "user", "password"),
        ),
        (
            "user:password@[2001:4800:7819:103:be76:4eff:fe04:9229]:22",
            HostSpec(
                "2001:4800:7819:103:be76:4eff:fe04:9229", "22", "user", "password"
            ),
        ),
    ],
)
def test_parse_hostspec(hostspec, expected):
    assert BaseBackend.parse_hostspec(hostspec) == expected


@pytest.mark.parametrize(
    "hostspec,pod,container,namespace,kubeconfig,context",
    [
        ("kubectl://pod", "pod", None, None, None, None),
        ("kubectl://pod?namespace=n", "pod", None, "n", None, None),
        ("kubectl://pod?container=c&namespace=n", "pod", "c", "n", None, None),
        ("kubectl://pod?namespace=n&kubeconfig=k", "pod", None, "n", "k", None),
        ("kubectl://pod?context=ctx&container=c", "pod", "c", None, None, "ctx"),
    ],
)
def test_kubectl_hostspec(
    hostspec,
    pod,
    container,
    namespace,
    kubeconfig,
    context,
):
    backend = testinfra.get_host(hostspec).backend
    assert backend.name == pod
    assert backend.container == container
    assert backend.namespace == namespace
    assert backend.kubeconfig == kubeconfig
    assert backend.context == context


@pytest.mark.parametrize(
    "hostspec,pod,container,namespace,kubeconfig",
    [
        ("openshift://pod", "pod", None, None, None),
        ("openshift://pod?namespace=n", "pod", None, "n", None),
        ("openshift://pod?container=c&namespace=n", "pod", "c", "n", None),
        ("openshift://pod?namespace=n&kubeconfig=k", "pod", None, "n", "k"),
    ],
)
def test_openshift_hostspec(hostspec, pod, container, namespace, kubeconfig):
    backend = testinfra.get_host(hostspec).backend
    assert backend.name == pod
    assert backend.container == container
    assert backend.namespace == namespace
    assert backend.kubeconfig == kubeconfig


@pytest.mark.parametrize(
    "arg_string,expected",
    [
        ("C:\\Users\\vagrant\\This Dir\\salt", '"C:\\Users\\vagrant\\This Dir\\salt"'),
        (
            "C:\\Users\\vagrant\\AppData\\Local\\Temp\\kitchen\\etc\\salt",
            '"C:\\Users\\vagrant\\AppData\\Local\\Temp\\kitchen\\etc\\salt"',
        ),
    ],
)
def test_winrm_quote(arg_string, expected):
    assert _quote(arg_string) == expected


@pytest.mark.parametrize(
    "hostspec,expected",
    [
        (
            "ssh://h",
            "ssh -o ConnectTimeout=10 -o ControlMaster=auto "
            "-o ControlPersist=60s h true",
        ),
        (
            "ssh://h?timeout=1",
            "ssh -o ConnectTimeout=1 -o ControlMaster=auto "
            "-o ControlPersist=60s h true",
        ),
        (
            "ssh://u@h:2222",
            "ssh -o User=u -o Port=2222 -o ConnectTimeout=10 "
            "-o ControlMaster=auto -o ControlPersist=60s h true",
        ),
        (
            "ssh://h:2222?ssh_config=/f",
            "ssh -F /f -o Port=2222 -o ConnectTimeout=10 "
            "-o ControlMaster=auto -o ControlPersist=60s h true",
        ),
        (
            "ssh://u@h?ssh_identity_file=/id",
            "ssh -o User=u -i /id -o ConnectTimeout=10 "
            "-o ControlMaster=auto -o ControlPersist=60s h true",
        ),
        (
            "ssh://h?controlpersist=1",
            "ssh -o ConnectTimeout=10 "
            "-o ControlMaster=auto -o ControlPersist=1s h true",
        ),
        ("ssh://h?controlpersist=0", "ssh -o ConnectTimeout=10 h true"),
    ],
)
def test_ssh_hostspec(hostspec, expected):
    backend = testinfra.get_host(hostspec).backend
    cmd, cmd_args = backend._build_ssh_command("true")
    command = backend.quote(" ".join(cmd), *cmd_args)
    assert command == expected


def test_get_hosts():
    # Hosts returned by get_host must be deduplicated (by name & kwargs) and in
    # same order as asked
    hosts = testinfra.backend.get_backends(
        [
            "ssh://foo",
            "ssh://a",
            "ssh://a",
            "ssh://a?timeout=1",
        ]
    )
    assert [(h.host.name, h.timeout) for h in hosts] == [
        ("foo", 10),
        ("a", 10),
        ("a", 1),
    ]
