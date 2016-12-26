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
        "debian_jessie", "centos_7", "ubuntu_trusty", "fedora",
        "ubuntu_xenial",
    )
])


@all_images
def test_package(docker_image, Package):
    ssh = Package("openssh-server")
    version = {
        "debian_jessie": "1:6.7",
        "debian_wheezy": "1:6.0",
        "fedora": "7.",
        "ubuntu_trusty": "1:6.6",
        "ubuntu_xenial": "1:7.2",
        "centos_7": "6.6",
    }[docker_image]
    assert ssh.is_installed
    assert ssh.version.startswith(version)
    release = {
        "fedora": "7.fc25",
        "centos_7": "31.el7",
        "debian_jessie": None,
        "debian_wheezy": None,
        "ubuntu_trusty": None,
        "ubuntu_xenial": None,
    }[docker_image]
    if release is None:
        with pytest.raises(NotImplementedError):
            ssh.release
    else:
        assert ssh.release.startswith(release)


def test_held_package(Package):
    python = Package("python")
    assert python.is_installed
    assert python.version.startswith("2.7.9")


@all_images
def test_systeminfo(docker_image, SystemInfo):
    assert SystemInfo.type == "linux"

    release, distribution, codename = {
        "debian_jessie": ("^8\.", "debian", "jessie"),
        "debian_wheezy": ("^7$", "debian", None),
        "centos_7": ("^7$", "centos", None),
        "fedora": ("^25$", "fedora", None),
        "ubuntu_trusty": ("^14\.04$", "ubuntu", "trusty"),
        "ubuntu_xenial": ("^16\.04$", "ubuntu", "xenial"),
    }[docker_image]

    assert SystemInfo.distribution == distribution
    assert SystemInfo.codename == codename
    assert re.match(release, SystemInfo.release)


@all_images
def test_ssh_service(docker_image, Service):
    if docker_image in ("centos_7", "fedora"):
        name = "sshd"
    else:
        name = "ssh"

    ssh = Service(name)
    if docker_image == "ubuntu_xenial":
        assert not ssh.is_running
    else:
        assert ssh.is_running

    if docker_image in ("ubuntu_trusty", "ubuntu_xenial"):
        assert not ssh.is_enabled
    else:
        assert ssh.is_enabled


@pytest.mark.parametrize("name,running,enabled", [
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


def test_salt(Salt):
    ssh_version = Salt("pkg.version", "openssh-server", local=True)
    assert ssh_version.startswith("1:6.7")


def test_puppet_resource(PuppetResource):
    resource = PuppetResource("package", "openssh-server")
    assert resource["openssh-server"]["ensure"].startswith("1:6.7")


def test_facter(Facter):
    assert Facter()["lsbdistcodename"] == "jessie"
    assert Facter("lsbdistcodename") == {
        "lsbdistcodename": "jessie",
    }


def test_sysctl(Sysctl, Command):
    assert Sysctl("kernel.hostname") == Command.check_output("hostname")
    assert isinstance(Sysctl("kernel.panic"), int)


def test_parse_socketspec():
    assert parse_socketspec("tcp://22") == ("tcp", None, 22)
    assert parse_socketspec("tcp://:::22") == ("tcp", "::", 22)
    assert parse_socketspec("udp://0.0.0.0:22") == ("udp", "0.0.0.0", 22)
    assert parse_socketspec("unix://can:be.any/thing:22") == (
        "unix", "can:be.any/thing:22", None)


def test_socket(TestinfraBackend, Socket):
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

    assert not Socket("tcp://4242").is_listening

    if not TestinfraBackend.get_connection_type() == "docker":
        # FIXME
        for spec in (
            "tcp://22",
            "tcp://0.0.0.0:22",
        ):
            assert len(Socket(spec).clients) >= 1


@all_images
def test_process(docker_image, Process):
    init = Process.get(pid=1)
    assert init.ppid == 0
    assert init.euid == 0

    args, comm = {
        "debian_jessie": ("/sbin/init", "systemd"),
        "centos_7": ("/usr/sbin/init", "systemd"),
        "fedora": ("/usr/sbin/init", "systemd"),
        "ubuntu_trusty": ("/usr/sbin/sshd -D", "sshd"),
        "ubuntu_xenial": ("/sbin/init", "systemd"),
        "debian_wheezy": ("/usr/sbin/sshd -D", "sshd"),
    }[docker_image]
    assert init.args == args
    assert init.comm == comm


def test_user(User):
    user = User("sshd")
    assert user.exists
    assert user.name == "sshd"
    assert user.uid == 105
    assert user.gid == 65534
    assert user.group == "nogroup"
    assert user.gids == [65534]
    assert user.groups == ["nogroup"]
    assert user.shell == "/usr/sbin/nologin"
    assert user.home == "/var/run/sshd"
    assert user.password == "*"


def test_user_user(User):
    user = User("user")
    assert user.exists
    assert user.gecos == "gecos.comment"


def test_user_expiration_date(User):
    assert User("root").expiration_date is None
    assert User("user").expiration_date == datetime.datetime(2024, 10, 4, 0, 0)


def test_nonexistent_user(User):
    assert not User("zzzzzzzzzz").exists


def test_current_user(User):
    assert User().name == "root"
    pw = User().password
    assert crypt.crypt("foo", pw) == pw


def test_group(Group):
    assert Group("root").exists
    assert Group("root").gid == 0


def test_empty_command_output(Command):
    assert Command.check_output("printf ''") == ""


def test_local_command(LocalCommand):
    assert LocalCommand.check_output("true") == ""


def test_file(Command, SystemInfo, File):
    Command.check_output("mkdir -p /d && printf foo > /d/f && chmod 600 /d/f")
    d = File("/d")
    assert d.is_directory
    assert not d.is_file
    f = File("/d/f")
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
    Command.check_output("ln -fsn /d/f /d/l")
    l = File("/d/l")
    assert l.is_symlink
    assert l.is_file
    assert l.linked_to == "/d/f"

    Command.check_output("rm -f /d/p && mkfifo /d/p")
    assert File("/d/p").is_pipe


def test_ansible_unavailable(Ansible):
    with pytest.raises(RuntimeError) as excinfo:
        Ansible("setup")
    assert (
        'Ansible module is only available with ansible '
        'connection backend') in str(excinfo.value)


@pytest.mark.testinfra_hosts("ansible://debian_jessie")
def test_ansible_module(TestinfraBackend, Ansible):
    import ansible
    version = int(ansible.__version__.split(".", 1)[0])
    setup = Ansible("setup")["ansible_facts"]
    assert setup["ansible_lsb"]["codename"] == "jessie"
    passwd = Ansible("file", "path=/etc/passwd state=file")
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

    variables = Ansible.get_variables()
    assert variables["myvar"] == "foo"
    assert variables["myhostvar"] == "bar"
    assert variables["mygroupvar"] == "qux"
    assert variables["inventory_hostname"] == "debian_jessie"
    assert variables["group_names"] == ["testgroup"]

    # test errors reporting
    with pytest.raises(Ansible.AnsibleException) as excinfo:
        Ansible("file", "path=/etc/passwd an_unexpected=variable")
    tb = str(excinfo.value)
    assert 'unsupported parameter for module: an_unexpected' in tb

    with pytest.raises(Ansible.AnsibleException) as excinfo:
        Ansible("command", "zzz")
    if version == 1:
        msg = "check mode not supported for command"
    else:
        msg = "Skipped. You might want to try check=False"
    assert excinfo.value.result['msg'] == msg

    try:
        Ansible("command", "zzz", check=False)
    except Ansible.AnsibleException as exc:
        assert exc.result['rc'] == 2
        if version == 1:
            assert exc.result['msg'] == '[Errno 2] No such file or directory'
        else:
            assert exc.result['msg'] == ('[Errno 2] Aucun fichier ou dossier '
                                         'de ce type')

    result = Ansible("command", "echo foo", check=False)
    assert result['stdout'] == 'foo'


@pytest.mark.destructive
def test_supervisor(Command, Service, Supervisor, Process):
    # Wait supervisord is running
    for _ in range(20):
        if Service("supervisor").is_running:
            break
        time.sleep(.5)
    else:
        raise RuntimeError("No running supervisor")

    for _ in range(20):
        service = Supervisor("tail")
        if service.status == "RUNNING":
            break
        else:
            assert service.status == "STARTING"
            time.sleep(.5)
    else:
        raise RuntimeError("No running tail in supervisor")

    assert service.is_running
    proc = Process.get(pid=service.pid)
    assert proc.comm == "tail"

    services = Supervisor.get_services()
    assert len(services) == 1
    assert services[0].name == "tail"
    assert services[0].is_running
    assert services[0].pid == service.pid

    Command("supervisorctl stop tail")
    service = Supervisor("tail")
    assert not service.is_running
    assert service.status == "STOPPED"
    assert service.pid is None

    Command("service supervisor stop")
    assert not Service("supervisor").is_running
    with pytest.raises(RuntimeError) as excinfo:
        Supervisor("tail").is_running
    assert 'Is supervisor running' in str(excinfo.value)


def test_mountpoint(MountPoint):
    root_mount = MountPoint('/')
    assert root_mount.exists
    assert isinstance(root_mount.options, list)
    assert 'rw' in root_mount.options
    assert root_mount.filesystem

    fake_mount = MountPoint('/fake/mount')
    assert not fake_mount.exists

    mountpoints = MountPoint.get_mountpoints()
    assert mountpoints
    assert all(isinstance(m, MountPoint) for m in mountpoints)
    assert len([m for m in mountpoints if m.path == "/"]) == 1


def test_sudo_from_root(Sudo, User):
    assert User().name == "root"
    with Sudo("user"):
        assert User().name == "user"
    assert User().name == "root"


@pytest.mark.testinfra_hosts("docker://user@debian_jessie")
def test_sudo_to_root(Sudo, User):
    assert User().name == "user"
    with Sudo():
        assert User().name == "root"
        # Test nested sudo
        with Sudo("www-data"):
            assert User().name == "www-data"
    assert User().name == "user"


def test_pip_package(PipPackage):
    assert PipPackage.get_packages()['pip']['version'] == '1.5.6'
    pytest = PipPackage.get_packages(pip_path='/v/bin/pip')['pytest']
    assert pytest['version'].startswith('2.')
    outdated = PipPackage.get_outdated_packages(
        pip_path='/v/bin/pip')['pytest']
    assert outdated['current'] == pytest['version']
    assert int(outdated['latest'].split('.')[0]) > 2
