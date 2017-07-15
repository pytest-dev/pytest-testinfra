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


try:
    import passlib.hash
    HAS_PASSLIB = True
except ImportError:
    HAS_PASSLIB = False

import crypt
import datetime
import mock
import pytest
import re
import testinfra
import time

from testinfra.modules.socket import parse_socketspec

all_images = pytest.mark.testinfra_hosts(*[
    "docker://{}".format(image)
    for image in (
        "debian_jessie", "centos_7", "ubuntu_trusty", "fedora",
        "ubuntu_xenial",
    )
])


@all_images
def test_package(host, docker_image):
    ssh = host.package("openssh-server")
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
        "fedora": ".fc25",
        "centos_7": ".el7",
        "debian_jessie": None,
        "debian_wheezy": None,
        "ubuntu_trusty": None,
        "ubuntu_xenial": None,
    }[docker_image]
    if release is None:
        with pytest.raises(NotImplementedError):
            ssh.release
    else:
        assert release in ssh.release


def test_held_package(host):
    python = host.package("python")
    assert python.is_installed
    assert python.version.startswith("2.7.9")


@all_images
def test_systeminfo(host, docker_image):
    assert host.system_info.type == "linux"

    release, distribution, codename = {
        "debian_jessie": ("^8\.", "debian", "jessie"),
        "debian_wheezy": ("^7$", "debian", None),
        "centos_7": ("^7$", "centos", None),
        "fedora": ("^25$", "fedora", None),
        "ubuntu_trusty": ("^14\.04$", "ubuntu", "trusty"),
        "ubuntu_xenial": ("^16\.04$", "ubuntu", "xenial"),
    }[docker_image]

    assert host.system_info.distribution == distribution
    assert host.system_info.codename == codename
    assert re.match(release, host.system_info.release)


@pytest.mark.testinfra_hosts("docker://debian_jessie")
def test_systeminfo__is_debian_returns_True_if_debian_based_host(host):
    assert host.system_info.is_debian


@pytest.mark.testinfra_hosts("docker://centos_7")
def test_systeminfo__is_debian_returns_False_if_not_debian_based_host(host):
    assert host.system_info.is_debian is False


@pytest.mark.testinfra_hosts("docker://debian_jessie")
def test_systeminfo__is_linux_returns_True_if_linux_host(host):
    assert host.system_info.is_linux


def test_systeminfo__is_darwin_returns_True_if_darwin_host():
    local = testinfra.get_host('local://').backend
    is_darwin = local.exists('sw_vers')
    if not is_darwin:
        pytest.skip('Skipping test because host is not Darwin')

    assert local.system_info.is_darwin


@pytest.mark.testinfra_hosts("docker://debian_jessie")
def test_systeminfo__is_darwin_returns_False_if_darwin_host(host):
    assert host.system_info.is_darwin is False


@pytest.mark.parametrize(
    'os_rel',
    [
        'CentOS',
        'Scientific Linux CERN',
        'Scientific Linux release',
        'CloudLinux',
        'Ascendos',
        'XenServer',
        'XCP',
        'Parallels Server Bare Metal',
        'Fedora release',
    ]
)
def test_systeminfo__is_redhat_returns_True_if_redhat_host(os_rel):
    # we use the local backend because we just need a backend and
    # we are going to mock the backend.sysinfo['distribution'] property.
    local = testinfra.get_host('local://').backend
    local.system_info.sysinfo['distribution'] = os_rel

    assert local.system_info.is_redhat


@pytest.mark.testinfra_hosts('docker://debian_jessie')
def test_systeminfo__is_redhat_returns_False_if_not_redhat_host(host):
    assert host.system_info.is_redhat is False


@pytest.mark.parametrize(
    'os_rel',
    [
        'freebsd',
    ],
)
def test_systeminfo__is_freebsd_returns_True_if_freebsd_host(os_rel):
    # we use the local backend because we just need a backend and
    # we are going to mock the backend.sysinfo['type'] property.
    local = testinfra.get_host('local://').backend
    local.system_info.sysinfo['type'] = os_rel

    assert local.system_info.is_freebsd


@pytest.mark.testinfra_hosts('docker://debian_jessie')
def test_systeminfo__is_freebsd_returns_False_if_not_freebsd_host(host):
    assert host.system_info.is_freebsd is False


@pytest.mark.parametrize(
    'os_rel',
    [
        'openbsd',
    ],
)
def test_systeminfo__is_openbsd_returns_True_if_openbsd_host(os_rel):
    # we use the local backend because we just need a backend and
    # we are going to mock the backend.sysinfo['type'] property.
    local = testinfra.get_host('local://').backend
    local.system_info.sysinfo['type'] = os_rel

    assert local.system_info.is_openbsd


@pytest.mark.testinfra_hosts('docker://debian_jessie')
def test_systeminfo__is_openbsd_returns_False_if_not_openbsd_host(host):
    assert host.system_info.is_openbsd is False


@pytest.mark.parametrize(
    'os_rel',
    [
        'netbsd',
    ],
)
def test_systeminfo__is_netbsd_returns_True_if_netbsd_host(os_rel):
    # we use the local backend because we just need a backend and
    # we are going to mock the backend.sysinfo['type'] property.
    local = testinfra.get_host('local://').backend
    local.system_info.sysinfo['type'] = os_rel

    assert local.system_info.is_netbsd


@pytest.mark.testinfra_hosts('docker://debian_jessie')
def test_systeminfo__is_netbsd_returns_False_if_not_netbsd_host(host):
    assert host.system_info.is_openbsd is False


@pytest.mark.parametrize(
    'os_rel',
    [
        'freebsd',
        'openbsd',
        'netbsd',
    ],
)
def test_systeminfo__is_bsd_returns_True_if_bsd_host(os_rel):
    # we use the local backend because we just need a backend and
    # we are going to mock the backend.sysinfo['type'] property.
    local = testinfra.get_host('local://').backend
    local.system_info.sysinfo['type'] = os_rel

    assert local.system_info.is_bsd


@pytest.mark.testinfra_hosts('docker://debian_jessie')
def test_systeminfo__is_bsd_returns_False_if_not_bsd_host(host):
    assert host.system_info.is_bsd is False


@pytest.mark.testinfra_hosts('docker://centos_7')
def test_systeminfo__has_systemd_returns_True(host):
    assert host.system_info.has_systemd


@pytest.mark.testinfra_hosts('docker://debian_wheezy')
def test_systeminfo__has_systemd_returns_False(host):
    assert host.system_info.has_systemd is False


@pytest.mark.testinfra_hosts('docker://debian_wheezy')
def test_systeminfo__has_service_returns_True(host):
    assert host.system_info.has_service


@pytest.mark.testinfra_hosts('docker://centos_7')
def test_systeminfo__has_service_returns_False(host):
    assert host.system_info.has_service is False


@pytest.mark.testinfra_hosts('docker://debian_wheezy')
def test_systeminfo__has_initctl_returns_True(host):
    assert host.system_info.has_initctl


@pytest.mark.testinfra_hosts('docker://centos_7')
def test_systeminfo__has_initctl_returns_False(host):
    assert host.system_info.has_initctl is False


@all_images
def test_ssh_service(host, docker_image):
    if docker_image in ("centos_7", "fedora"):
        name = "sshd"
    else:
        name = "ssh"

    ssh = host.service(name)
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
def test_service(host, name, running, enabled):
    service = host.service(name)
    assert service.is_running == running
    assert service.is_enabled == enabled


def test_salt(host):
    ssh_version = host.salt("pkg.version", "openssh-server", local=True)
    assert ssh_version.startswith("1:6.7")


def test_puppet_resource(host):
    resource = host.puppet_resource("package", "openssh-server")
    assert resource["openssh-server"]["ensure"].startswith("1:6.7")


def test_facter(host):
    assert host.facter()["lsbdistcodename"] == "jessie"
    assert host.facter("lsbdistcodename") == {
        "lsbdistcodename": "jessie",
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


class Test__DarwinSocket(object):

    @pytest.fixture
    def simulate_darwin(self):
        self.local = testinfra.get_host('local://').backend
        self.local.system_info.sysinfo["type"] = 'darwin'

    @pytest.fixture
    def invalid_dgram_entries(self, simulate_darwin):
        return (
            'udp4       0      0  *.*                    *.*\n'
            'udp4       0      0  *.*                    *.*\n'
            'udp4       0      0  *.*                    *.*\n'
            'udp4       0      0  *.*                    *.*\n'
        )

    @pytest.fixture
    def valid_sockets(self, simulate_darwin):
        def on_call(return_tcp=True, return_udp=True, return_unix=False):
            tcp = (
                'tcp4       0      0  127.0.0.1.51096     127.0.0.0.443      ESTABLISHED\n'  # noqa: E501
                'tcp4       0      0  127.0.0.1.51097     127.0.0.0.443      CLOSE_WAIT\n'  # noqa: E501
                'tcp4       0      0  *.1002                 *.*             LISTEN\n'  # noqa: E501
                'tcp6       0      0  *.17500                *.*             LISTEN\n'  # noqa: E501
                'tcp6       0      0  *.997                  *.*             LISTEN\n'  # noqa: E501
                'tcp6       0      0  ::1.53                 *.*             LISTEN\n'  # noqa: E501
                'tcp6       0      0  fe80::1%lo0.53         *.*             LISTEN\n'  # noqa: E501
            )

            udp = (
                'udp6       0      0  *.50935                *.*\n'
                'udp6       0      0  fe80::544c:9902:.123   *.*\n'
                'udp6       0      0  ::1.123                *.*\n'
                'udp4       0      0  *.50935                *.*\n'
                'udp4       0      0  127.0.0.1.123          *.*\n'
            )

            unix = (
                'Active LOCAL (UNIX) domain sockets\n'
                'Address          Type   Recv-Q Send-Q            Inode             Conn             Refs          Nextref Addr\n'  # noqa: E501
                'eae3c6f3ba092ced stream      0      0                0 eae3c6f3ba092db5                0                0 /var/run/mDNSResponder\n'  # noqa: E501
                'eae3c6f3ba092db5 stream      0      0                0 eae3c6f3ba092ced                0                0\n'  # noqa: E501
                'eae3c6f3ba0937dd stream      0      0                0 eae3c6f3ba09332d                0                0\n'  # noqa: E501
                'eae3c6f3bbb93a35 stream      0      0 eae3c6f3b5d9fc15                0                0                0 /tmp/.vbox-codylane-ipc/ipcd\n'  # noqa: E501
                'eae3c6f3b1b89205 stream      0      0                0 eae3c6f3b1b867d5                0                0 /var/run/mDNSResponder\n'  # noqa: E501
                'eae3c6f3ba092a95 dgram       0      0                0 eae3c6f3b1b87b5d                0 eae3c6f3ba092c25\n'  # noqa: E501
                'eae3c6f3b1b87b5d dgram       0      0 eae3c6f3b1b762dd                0 eae3c6f3ba092a95                0 /private//var/run/syslog\n'  # noqa: E501
            )

            if return_tcp and return_udp and return_unix:
                return tcp + udp + unix

            if return_tcp and return_udp:
                return tcp + udp

            if return_tcp and return_unix:
                return tcp + unix

            if return_udp and return_unix:
                return udp + unix

            if return_tcp:
                return tcp

            if return_udp:
                return udp

            if return_unix:
                return unix

            raise NotImplementedError

        return on_call

    def test__get_sockets__will_return_empty_list_when_dgram_entries_are_all_wildcards(self, invalid_dgram_entries):  # noqa: E501
        with mock.patch.object(self.local.socket, 'check_output', autospec=True, return_value=invalid_dgram_entries) as mocked_method:  # noqa: E501
            socket = self.local.socket(None)
            actual_sockets = socket.get_sockets(True)

            assert isinstance(actual_sockets, list)
            assert len(actual_sockets) == 0

        mocked_method.assert_called_once_with(socket, 'netstat -n -a')

    def test__get_sockets__will_return_non_empty_list_when_dgram_entries(self, valid_sockets):  # noqa: E501
        with mock.patch.object(self.local.socket, 'check_output', autospec=True, return_value=valid_sockets) as mocked_method:  # noqa: E501
            socket = self.local.socket(None)
            actual_sockets = socket.get_sockets(True)

            expected = [
                ('tcp', '0.0.0.0', 1002),
                ('tcp', '::', 17500),
                ('tcp', '::', 997),
                ('tcp', '::1', 53),
                ('tcp', 'fe80::1%lo0', 53),
                ('udp', '::', 50935),
                ('udp', 'fe80::544c:9902:', 123),
                ('udp', '::1', 123),
                ('udp', '0.0.0.0', 50935),
                ('udp', '127.0.0.1', 123),
            ]

            assert isinstance(actual_sockets, list)
            assert actual_sockets == expected


@all_images
def test_process(host, docker_image):
    init = host.process.get(pid=1)
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


def test_user(host):
    user = host.user("sshd")
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

    # when HAS_PASSLIB = True, it's probably because the host OS is OSX.
    # OSX requires the use of passlib over crypt becuase OSX ships a very old
    # version of crypt and it doesn't support the proper hash length for sha512
    if HAS_PASSLIB:
        assert passlib.hash.sha512_crypt.verify('foo', pw)
    else:
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

    host.check_output("rm -f /d/p && mkfifo /d/p")
    assert host.file("/d/p").is_pipe


def test_ansible_unavailable(host):
    with pytest.raises(RuntimeError) as excinfo:
        host.ansible("setup")
    assert (
        'Ansible module is only available with ansible '
        'connection backend') in str(excinfo.value)


@pytest.mark.testinfra_hosts("ansible://debian_jessie")
def test_ansible_module(host):
    import ansible
    version = int(ansible.__version__.split(".", 1)[0])
    setup = host.ansible("setup")["ansible_facts"]
    assert setup["ansible_lsb"]["codename"] == "jessie"
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
    assert variables["inventory_hostname"] == "debian_jessie"
    assert variables["group_names"] == ["testgroup"]

    # test errors reporting
    with pytest.raises(host.ansible.AnsibleException) as excinfo:
        host.ansible("file", "path=/etc/passwd an_unexpected=variable")
    tb = str(excinfo.value)
    assert 'unsupported parameter' in tb.lower()

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


@pytest.mark.testinfra_hosts("docker://user@debian_jessie")
def test_sudo_to_root(host):
    assert host.user().name == "user"
    with host.sudo():
        assert host.user().name == "root"
        # Test nested sudo
        with host.sudo("www-data"):
            assert host.user().name == "www-data"
    assert host.user().name == "user"


def test_pip_package(host):
    assert host.pip_package.get_packages()['pip']['version'] == '1.5.6'
    pytest = host.pip_package.get_packages(pip_path='/v/bin/pip')['pytest']
    assert pytest['version'].startswith('2.')
    outdated = host.pip_package.get_outdated_packages(
        pip_path='/v/bin/pip')['pytest']
    assert outdated['current'] == pytest['version']
    assert int(outdated['latest'].split('.')[0]) > 2
