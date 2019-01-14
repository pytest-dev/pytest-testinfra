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

import crypt
import datetime
import re
import time

import pytest
from testinfra.modules.socket import parse_socketspec

all_images = pytest.mark.testinfra_hosts(*[
    "docker://{}".format(image)
    for image in (
        "alpine_38", "archlinux", "centos_6", "centos_7",
        "debian_stretch", "ubuntu_xenial"
    )
])


@all_images
def test_package(host, docker_image):
    assert not host.package('zsh').is_installed
    if docker_image in ("alpine_38", "archlinux"):
        name = "openssh"
    else:
        name = "openssh-server"

    ssh = host.package(name)
    version = {
        "alpine_38": "7.",
        "archlinux": "7.",
        "centos_6": "5.",
        "centos_7": "7.",
        "debian_stretch": "1:7.4",
        "ubuntu_xenial": "1:7.2"
    }[docker_image]
    assert ssh.is_installed
    assert ssh.version.startswith(version)
    release = {
        "alpine_38": "r3",
        "archlinux": None,
        "centos_6": ".el6",
        "centos_7": ".el7",
        "debian_stretch": None,
        "ubuntu_xenial": None
    }[docker_image]
    if release is None:
        with pytest.raises(NotImplementedError):
            ssh.release
    else:
        assert release in ssh.release


def test_held_package(host):
    python = host.package("python")
    assert python.is_installed
    assert python.version.startswith("2.7.")


@pytest.mark.destructive
def test_uninstalled_package_version(host):
    with pytest.raises(AssertionError) as excinfo:
        host.package('zsh').version
    assert 'Unexpected exit code 1 for CommandResult' in str(excinfo.value)
    assert host.package('sudo').is_installed
    host.check_output('apt-get -y remove sudo')
    assert not host.package('sudo').is_installed
    with pytest.raises(AssertionError) as excinfo:
        host.package('sudo').version
    assert ('The package sudo is not installed, dpkg-query output: '
            'deinstall ok config-files 1.8.') in str(excinfo.value)


@all_images
def test_systeminfo(host, docker_image):
    assert host.system_info.type == "linux"

    release, distribution, codename = {
        "alpine_38": ("^3\.8\.", "alpine", None),
        "archlinux": ("rolling", "arch", None),
        "centos_6": (r"^6", "CentOS", None),
        "centos_7": ("^7$", "centos", None),
        "debian_stretch": ("^9\.", "debian", "stretch"),
        "ubuntu_xenial": ("^16\.04$", "ubuntu", "xenial")
    }[docker_image]

    assert host.system_info.distribution == distribution
    assert host.system_info.codename == codename
    assert re.match(release, host.system_info.release)


@all_images
def test_ssh_service(host, docker_image):
    if docker_image in ("centos_6", "centos_7",
                        "alpine_38", "archlinux"):
        name = "sshd"
    else:
        name = "ssh"

    ssh = host.service(name)
    if docker_image == "ubuntu_xenial":
        assert not ssh.is_running
    # FIXME: is_running test is broken for archlinux for unknown reason
    elif docker_image != "archlinux":
        assert ssh.is_running

    if docker_image == "ubuntu_xenial":
        assert not ssh.is_enabled
    else:
        assert ssh.is_enabled


@pytest.mark.parametrize("name,running,enabled", [
    ("ntp", False, True),
    ("salt-minion", False, False),
])
def test_service(host, name, running, enabled):
    service = host.service(name)
    assert service.is_running == running
    assert service.is_enabled == enabled


def test_salt(host):
    ssh_version = host.salt("pkg.version", "openssh-server", local=True)
    assert ssh_version.startswith("1:7.4")


def test_puppet_resource(host):
    resource = host.puppet_resource("package", "openssh-server")
    assert resource["openssh-server"]["ensure"].startswith("1:7.4")


def test_facter(host):
    assert host.facter()["lsbdistcodename"] == "stretch"
    assert host.facter("lsbdistcodename") == {
        "lsbdistcodename": "stretch",
    }


def test_sysctl(host):
    assert host.sysctl("kernel.hostname") == host.check_output("hostname")
    assert isinstance(host.sysctl("kernel.panic"), int)


def test_parse_socketspec():
    assert parse_socketspec("tcp://22") == ("tcp", None, 22)
    assert parse_socketspec("tcp://:::22") == ("tcp", "::", 22)
    assert parse_socketspec("udp://0.0.0.0:22") == ("udp", "0.0.0.0", 22)
    assert parse_socketspec("unix://can:be.any/thing:22") == (
        "unix", "can:be.any/thing:22", None)


def test_socket(host):
    listening = host.socket.get_listening_sockets()
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
        "unix:///run/systemd/private",
    ):
        socket = host.socket(spec)
        assert socket.is_listening

    assert not host.socket("tcp://4242").is_listening

    if not host.backend.get_connection_type() == "docker":
        # FIXME
        for spec in (
            "tcp://22",
            "tcp://0.0.0.0:22",
        ):
            assert len(host.socket(spec).clients) >= 1


@all_images
def test_process(host, docker_image):
    init = host.process.get(pid=1)
    assert init.ppid == 0
    if docker_image != "alpine_38":
        # busybox ps doesn't have a euid equivalent
        assert init.euid == 0
    assert init.user == "root"

    args, comm = {
        "alpine_38": ("/sbin/init", "init"),
        "archlinux": ("/usr/sbin/init", "systemd"),
        "centos_6": ("/usr/sbin/sshd -D", "sshd"),
        "centos_7": ("/usr/sbin/init", "systemd"),
        "debian_stretch": ("/sbin/init", "systemd"),
        "ubuntu_xenial": ("/sbin/init", "systemd")
    }[docker_image]
    assert init.args == args
    assert init.comm == comm


def test_user(host):
    user = host.user("sshd")
    assert user.exists
    assert user.name == "sshd"
    assert user.uid == 107
    assert user.gid == 65534
    assert user.group == "nogroup"
    assert user.gids == [65534]
    assert user.groups == ["nogroup"]
    assert user.shell == "/usr/sbin/nologin"
    assert user.home == "/run/sshd"
    assert user.password == "*"


def test_user_user(host):
    user = host.user("user")
    assert user.exists
    assert user.gecos == "gecos.comment"


def test_user_expiration_date(host):
    assert host.user("root").expiration_date is None
    assert host.user("user").expiration_date == (
        datetime.datetime(2024, 10, 4, 0, 0))


def test_nonexistent_user(host):
    assert not host.user("zzzzzzzzzz").exists


def test_current_user(host):
    assert host.user().name == "root"
    pw = host.user().password
    assert crypt.crypt("foo", pw) == pw


def test_group(host):
    assert host.group("root").exists
    assert host.group("root").gid == 0


def test_empty_command_output(host):
    assert host.check_output("printf ''") == ""


def test_local_command(host):
    assert host.get_host("local://").check_output("true") == ""


def test_file(host):
    host.check_output("mkdir -p /d && printf foo > /d/f && chmod 600 /d/f")
    d = host.file("/d")
    assert d.is_directory
    assert not d.is_file
    f = host.file("/d/f")
    assert f.exists
    assert f.is_file
    assert f.content == b"foo"
    assert f.content_string == "foo"
    assert f.user == "root"
    assert f.uid == 0
    assert f.gid == 0
    assert f.group == "root"
    assert f.mode == 0o600
    assert f.contains("fo")
    assert not f.is_directory
    assert not f.is_symlink
    assert not f.is_pipe
    assert f.linked_to == "/d/f"
    assert f.size == 3
    assert f.md5sum == "acbd18db4cc2f85cedef654fccc4a4d8"
    assert f.sha256sum == (
        "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
    )
    host.check_output("ln -fsn /d/f /d/l")
    l = host.file("/d/l")
    assert l.is_symlink
    assert l.is_file
    assert l.linked_to == "/d/f"
    assert l.linked_to == f
    assert f == host.file('/d/f')
    assert not d == f

    host.check_output("rm -f /d/p && mkfifo /d/p")
    assert host.file("/d/p").is_pipe


def test_ansible_unavailable(host):
    expected = ('Ansible module is only available with '
                'ansible connection backend')
    with pytest.raises(RuntimeError) as excinfo:
        host.ansible("setup")
    assert expected in str(excinfo.value)
    with pytest.raises(RuntimeError) as excinfo:
        host.ansible.get_variables()
    assert expected in str(excinfo.value)


@pytest.mark.testinfra_hosts("ansible://debian_stretch")
def test_ansible_module(host):
    import ansible
    version = int(ansible.__version__.split(".", 1)[0])
    setup = host.ansible("setup")["ansible_facts"]
    assert setup["ansible_lsb"]["codename"] == "stretch"
    passwd = host.ansible("file", "path=/etc/passwd state=file")
    assert passwd["changed"] is False
    assert passwd["gid"] == 0
    assert passwd["group"] == "root"
    assert passwd["mode"] == "0644"
    assert passwd["owner"] == "root"
    assert isinstance(passwd["size"], int)
    assert passwd["path"] == "/etc/passwd"
    # seems to vary with differents docker fs backend
    assert passwd["state"] in ("file", "hard")
    assert passwd["uid"] == 0

    variables = host.ansible.get_variables()
    assert variables["myvar"] == "foo"
    assert variables["myhostvar"] == "bar"
    assert variables["mygroupvar"] == "qux"
    assert variables["inventory_hostname"] == "debian_stretch"
    assert variables["group_names"] == ["testgroup"]

    with pytest.raises(host.ansible.AnsibleException) as excinfo:
        host.ansible("command", "zzz")
    if version == 1:
        msg = "check mode not supported for command"
    else:
        msg = "Skipped. You might want to try check=False"
    assert excinfo.value.result['msg'] == msg

    try:
        host.ansible("command", "zzz", check=False)
    except host.ansible.AnsibleException as exc:
        assert exc.result['rc'] == 2
        if version == 1:
            assert exc.result['msg'] == '[Errno 2] No such file or directory'
        else:
            assert exc.result['msg'] == ('[Errno 2] Aucun fichier ou dossier '
                                         'de ce type')

    result = host.ansible("command", "echo foo", check=False)
    assert result['stdout'] == 'foo'


@pytest.mark.testinfra_hosts("ansible://debian_stretch",
                             "ansible://user@debian_stretch")
def test_ansible_module_become(host):
    user_name = host.user().name
    assert host.ansible('shell', 'echo $USER',
                        check=False)['stdout'] == user_name
    assert host.ansible('shell', 'echo $USER',
                        check=False, become=True)['stdout'] == 'root'

    with host.sudo():
        assert host.user().name == 'root'
        assert host.ansible('shell', 'echo $USER',
                            check=False)['stdout'] == user_name
        assert host.ansible('shell', 'echo $USER',
                            check=False, become=True)['stdout'] == 'root'


@pytest.mark.destructive
def test_supervisor(host):
    # Wait supervisord is running
    for _ in range(20):
        if host.service("supervisor").is_running:
            break
        time.sleep(.5)
    else:
        raise RuntimeError("No running supervisor")

    for _ in range(20):
        service = host.supervisor("tail")
        if service.status == "RUNNING":
            break
        else:
            assert service.status == "STARTING"
            time.sleep(.5)
    else:
        raise RuntimeError("No running tail in supervisor")

    assert service.is_running
    proc = host.process.get(pid=service.pid)
    assert proc.comm == "tail"

    services = host.supervisor.get_services()
    assert len(services) == 1
    assert services[0].name == "tail"
    assert services[0].is_running
    assert services[0].pid == service.pid

    host.run("supervisorctl stop tail")
    service = host.supervisor("tail")
    assert not service.is_running
    assert service.status == "STOPPED"
    assert service.pid is None

    host.run("service supervisor stop")
    assert not host.service("supervisor").is_running
    with pytest.raises(RuntimeError) as excinfo:
        host.supervisor("tail").is_running
    assert 'Is supervisor running' in str(excinfo.value)


def test_mountpoint(host):
    root_mount = host.mount_point('/')
    assert root_mount.exists
    assert isinstance(root_mount.options, list)
    assert 'rw' in root_mount.options
    assert root_mount.filesystem

    fake_mount = host.mount_point('/fake/mount')
    assert not fake_mount.exists

    mountpoints = host.mount_point.get_mountpoints()
    assert mountpoints
    assert all(isinstance(m, host.mount_point) for m in mountpoints)
    assert len([m for m in mountpoints if m.path == "/"]) == 1


def test_sudo_from_root(host):
    assert host.user().name == "root"
    with host.sudo("user"):
        assert host.user().name == "user"
    assert host.user().name == "root"


def test_sudo_fail_from_root(host):
    assert host.user().name == "root"
    with pytest.raises(AssertionError) as exc:
        with host.sudo("unprivileged"):
            assert host.user().name == "unprivileged"
            host.check_output('ls /root/invalid')
    assert str(exc.value).startswith('Unexpected exit code')
    with host.sudo():
        assert host.user().name == "root"


@pytest.mark.testinfra_hosts("docker://user@debian_stretch")
def test_sudo_to_root(host):
    assert host.user().name == "user"
    with host.sudo():
        assert host.user().name == "root"
        # Test nested sudo
        with host.sudo("www-data"):
            assert host.user().name == "www-data"
    assert host.user().name == "user"


def test_command_execution(host):
    assert host.run("false").failed
    assert host.run("true").succeeded


def test_pip_package(host):
    assert host.pip_package.get_packages()['pip']['version'] == '9.0.1'
    pytest = host.pip_package.get_packages(pip_path='/v/bin/pip')['pytest']
    assert pytest['version'].startswith('2.')
    outdated = host.pip_package.get_outdated_packages(
        pip_path='/v/bin/pip')['pytest']
    assert outdated['current'] == pytest['version']
    assert int(outdated['latest'].split('.')[0]) > 2


def test_iptables(host):
    ssh_rule_str = \
        '-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT'
    vip_redirect_rule_str = \
        '-A PREROUTING -d 192.168.0.1/32 -j REDIRECT'
    rules = host.iptables.rules()
    input_rules = host.iptables.rules('filter', 'INPUT')
    nat_rules = host.iptables.rules('nat')
    nat_prerouting_rules = host.iptables.rules('nat', 'PREROUTING')
    assert ssh_rule_str in rules
    assert ssh_rule_str in input_rules
    assert vip_redirect_rule_str in nat_rules
    assert vip_redirect_rule_str in nat_prerouting_rules
    # test ip6tables call works; ipv6 setup is a whole huge thing, but
    # ensure we at least see the headings
    v6_rules = host.iptables.rules(version=6)
    assert '-P INPUT ACCEPT' in v6_rules
    assert '-P FORWARD ACCEPT' in v6_rules
    assert '-P OUTPUT ACCEPT' in v6_rules
    v6_filter_rules = host.iptables.rules('filter', 'INPUT', version=6)
    assert '-P INPUT ACCEPT' in v6_filter_rules
