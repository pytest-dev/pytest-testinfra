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
import mock
import os
import pytest
import six
import time

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
def test_command(host):
    assert host.check_output("true") == ""
    # test that quotting is correct
    assert host.run("echo a b | grep -q %s", "a c").rc == 1


@pytest.mark.testinfra_hosts(*HOSTS)
def test_encoding(host):
    if host.backend.get_connection_type() == "ansible":
        pytest.skip("ansible handle encoding himself")

    # jessie image is fr_FR@ISO-8859-15
    cmd = host.run("ls -l %s", "/é")
    if host.backend.get_connection_type() == "docker":
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
def test_user_connection(host):
    assert host.user().name == "user"


@pytest.mark.testinfra_hosts(*SUDO_HOSTS)
def test_sudo(host):
    assert host.user().name == "root"


@pytest.mark.testinfra_hosts("ansible://debian_jessie")
def test_ansible_hosts_expand(host):
    from testinfra.backend.ansible import AnsibleBackend

    def get_hosts(spec):
        return AnsibleBackend.get_hosts(
            spec, ansible_inventory=host.backend.ansible_inventory)
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


@pytest.mark.testinfra_hosts("docker://centos_7", "ssh://centos_7")
def test_docker_encoding(host):
    encoding = host.check_output(
        "python -c 'import locale;print(locale.getpreferredencoding())'")
    assert encoding == "ANSI_X3.4-1968"
    string = "ťēꞩƫìṇḟřặ ṧꝕèȃǩ ửƫᵮ8"
    assert host.check_output("echo %s | tee /tmp/s.txt", string) == string
    assert host.file("/tmp/s.txt").content_string.strip() == string


@pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
def test_vagrant__run_command_in_directory__will_change_directory_when_path_is_a_directory(vagrant_sut):
    from testinfra.backend import vagrant
    box = vagrant_sut(start=False)

    orig_dir = os.getcwd()
    expected_dir = os.path.dirname(orig_dir + '/' + box.vagrantfile)
    with vagrant.run_command_in_directory(box.vagrantfile):
        assert os.getcwd() == expected_dir
        assert orig_dir != os.getcwd()

    assert os.getcwd() == orig_dir


class Test__VagrantBackend__initialization(object):
    @pytest.mark.parametrize('init_kwargs,expected', [
        [
            dict(user='foo', vagrantfile='/vagrant/foo', box='default', status_refresh_interval=1),
            dict(user='foo', vagrantfile='/vagrant/foo/Vagrantfile', box='default', status_refresh_interval=1)
        ],
    ])
    def test__init__with_custom_args(self, init_kwargs, expected):

        hostspec = init_kwargs['user'] + '@' + init_kwargs['box']
        bkend = testinfra.get_host(hostspec, connection='vagrant', **init_kwargs).backend

        assert bkend.user == expected['user']
        assert bkend.vagrantfile == expected['vagrantfile']
        assert bkend.box == expected['box']
        assert bkend.status_refresh_interval == expected['status_refresh_interval']


def test_vagrant__call__will_return_a_new_VagrantBackend():

    kw = dict(connection='vagrant',
              vagrantfile='vagrant/ubuntu-trusty',
              user='vagrant',
              box='default',
              )

    hostspec = kw['user'] + '@' + kw['box']
    vagrant = testinfra.get_host('vagrant@default', **kw).backend
    result = vagrant(hostspec, **kw)

    assert result is not None
    assert result.user == kw['user']
    assert result.box == kw['box']
    assert result.vagrantfile == kw['vagrantfile'] + '/Vagrantfile'


def test_vagrant__get_hosts__will_return_array_of_hosts():
    host = testinfra.get_host('vagrant@default', connection='vagrant').backend

    result = host.get_hosts(host)
    assert len(result) == 1
    assert result == [host]


@pytest.mark.parametrize('hostspec, expected', [
    ('vagrant@default', 'vagrant@default'),
    ('vagrant', 'vagrant@vagrant'),
    ('@mybox', 'vagrant@mybox'),
    ('foo@', 'foo@default'),
])
def test_vagrant__hostspec__will_return__user_at_host__(hostspec, expected):
    host = testinfra.get_host(hostspec, connection='vagrant').backend
    assert host.hostspec == expected


@pytest.mark.vagrant_sut('vagrant://vagrant@default', vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
def test__vagrant_up__will_start_a_non_running_instance(vagrant_sut):
    vagrant = vagrant_sut(start=False, keep_running=True)
    vagrant.up
    assert vagrant.status.is_running


@pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
def test_vagrant_get_pytest_id_returns_vagrant(vagrant_sut):
    vagrant = vagrant_sut(start=False)
    assert vagrant.get_pytest_id() == 'vagrant'


class Test__VagrantBackend__status_method(object):

    def _method_called_counter(self, fn):
        def wrapper(*args, **kwargs):
            wrapper.called += 1
            return fn(*args, **kwargs)
        wrapper.called = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @pytest.fixture
    def mocked_status_refresh(self, vagrant_sut):
        self.vagrant = vagrant_sut(start=False)
        self.vagrant.expire_status_cache()

        def reset_counter():
            self.vagrant._refresh_status.called = 0

        self.vagrant._refresh_status = self._method_called_counter(self.vagrant._refresh_status)
        reset_counter()
        yield self.vagrant._refresh_status
        reset_counter()
        assert self.vagrant._refresh_status.called == 0

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test_when_invoked_twice_before_the_status_refresh_interval_expires(self, vagrant_sut, mocked_status_refresh):
        """SCENARIO: When invoking `vagrant.status` twice before the status refresh interval expires

        It should:
            - Store the current time in seconds in vagrant._last_refreshed
            - and not invoke vagrant._refresh_status() a second time

        """
        first_status = self.vagrant.status.is_running
        second_status = self.vagrant.status.is_running

        assert self.vagrant._refresh_status.called == 1
        assert first_status == second_status
        assert first_status is not None

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test_when_invoking_a_second_time_but_after_the_status_refresh_interval_expires(self, vagrant_sut, mocked_status_refresh):
        """SCENARIO: When invoking `vagrant.status` a second time but after the status refresh interval expires

        It should:
            - Store the current time in seconds in vagrant._last_refreshed
            - and not invoke vagrant._refresh_status() a second time

        """

        self.vagrant.status_refresh_interval = .5

        first_status = self.vagrant.status
        time.sleep(1)  # expire timer
        second_status = self.vagrant.status

        assert self.vagrant._refresh_status.called == 2
        assert first_status != second_status
        assert first_status is not None
        assert second_status is not None


class Test__VagrantBackend__when_vm_should_stay_running_after_each_test(object):

    @pytest.fixture
    def stay_running(self, vagrant_sut):
        self.vagrant = vagrant_sut(start=True, keep_running=True)

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__run__will_not_raise_error(self, stay_running):
        result = self.vagrant.run('vagrant status')
        assert result != ''
        assert result is not None

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__ssh_config_to_tmpfile__should_return_tempfile_with_saved_sshconfig_when_vm_is_powered_on(self, stay_running):
        actual_result = self.vagrant.ssh_config_to_tmpfile
        assert os.path.isfile(actual_result)
        assert os.stat(actual_result).st_mode & int('0o0777', 8) == 384

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__ssh_config__will_return_ssh_config_string_when_vm_is_powered_on(self, stay_running):
        actual_ssh_config = self.vagrant.ssh_config

        local = testinfra.get_host('local://').backend
        orig_dir = os.getcwd()
        os.chdir(os.path.dirname(self.vagrant.vagrantfile))
        expected_ssh_config = local.run('vagrant ssh-config ' + self.vagrant.box).stdout.strip()
        os.chdir(orig_dir)

        assert actual_ssh_config == expected_ssh_config

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__run_box__will_run_a_command_inside_vagrant_box_and_return_result(self, stay_running):
        whoami = self.vagrant.run_box('whoami')

        assert whoami.rc == 0
        assert whoami.stdout.strip() == 'vagrant'

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__communicate__will_return_paramiko_backend(self, stay_running):
        ssh = self.vagrant.communicate
        assert ssh.backend.NAME == 'paramiko'
        assert ssh.run('whoami').rc == 0
        assert ssh.run('whoami').stdout.strip() == 'vagrant'

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__vagrant_suspend__will_suspend_a_running_instance(self, stay_running):
        self.vagrant.suspend
        assert self.vagrant.status.is_not_running

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__vagrant_halt__will_stop_a_running_instance(self, stay_running):
        self.vagrant.halt
        assert self.vagrant.status.is_not_running


class Test__VagrantBackend__destructive_vm_tests(object):

    @pytest.fixture
    def reset_vagrant(self, vagrant_sut):
        self.vagrant = vagrant_sut(start=False, keep_running=False)

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__ssh_config__should_raise__AssertionError__when_vm_is_powered_off(self, reset_vagrant):
        with pytest.raises(AssertionError):
            self.vagrant.ssh_config

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__ssh_config_to_tmpfile__should_raise__AssertionError__when_vm_is_powered_off(self, reset_vagrant):
        with pytest.raises(AssertionError):
            self.vagrant.ssh_config_to_tmpfile

    @pytest.mark.vagrant_sut(vagrantfile='vagrant/ubuntu-trusty/Vagrantfile')
    def test__destroy__will_destroy_an_existing_vm(self, reset_vagrant):
        assert self.vagrant.status.is_created

        # we assume vagrant does the right thing here, so we just patch the method call
        # that would otherwise invoke the destroy command and make an assertion that the call
        # signature looks correct.
        with mock.patch.object(self.vagrant, 'run_vagrant', autospec=True) as mocked_method:
            self.vagrant.destroy
            mocked_method.assert_called_once_with('vagrant destroy default --force')
