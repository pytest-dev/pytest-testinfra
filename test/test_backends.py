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
import os
import pytest
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


def test_VagrantBackend__run_command_in_directory__will_change_directory_when_path_is_a_directory(mock_vagrant_backend):
    from testinfra.backend import vagrant

    # this may not be obvious which is why this message is here but we aren't actually
    # mocking the run_vagrant method.   We just have to mock something I chose for no
    # particular reason.
    box, run_vagrant_mock = mock_vagrant_backend('run_vagrant', autospec=True)

    orig_dir = os.getcwd()
    expected_dir = os.path.join(orig_dir, box.vagrantfile)
    with vagrant.run_command_in_directory(box.vagrantfile):
        assert os.getcwd() == os.path.dirname(expected_dir)
        assert orig_dir != os.getcwd()

    assert os.getcwd() == orig_dir


@pytest.mark.parametrize('init_kwargs,expected', [
    [
        dict(user='foo', vagrantfile='/vagrant/foo', box='default', status_refresh_interval=1),
        dict(user='foo', vagrantfile='/vagrant/foo/Vagrantfile', box='default', status_refresh_interval=1)
    ],
])
def test_VagrantBackend__init__with_custom_args(init_kwargs, expected):
    hostspec = init_kwargs['user'] + '@' + init_kwargs['box']
    bkend = testinfra.get_host(hostspec, connection='vagrant', **init_kwargs).backend

    assert bkend.user == expected['user']
    assert bkend.vagrantfile == expected['vagrantfile']
    assert bkend.box == expected['box']
    assert bkend.status_refresh_interval == expected['status_refresh_interval']


def test_VagrantBackend__call__will_return_a_new_VagrantBackend():
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


def test_VagrantBackend__get_hosts__will_return_array_of_hosts():
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
def test_VagrantBackend__hostspec__will_return__user_at_host__(hostspec, expected):
    host = testinfra.get_host(hostspec, connection='vagrant').backend
    assert host.hostspec == expected


def test_VagrantBackend_up__method_will_invoke_run_vagrant_with__vagrant_up_default(mock_vagrant_backend):
    vagrant, m1 = mock_vagrant_backend('run_vagrant', autospec=True)

    vagrant.up
    m1.assert_any_call('vagrant up %s', 'default')


def test_VagrantBackend_get_pytest_id_returns_vagrant(mock_vagrant_backend):
    hostspec = 'vagrant@default'
    vagrant = testinfra.get_host(hostspec, connection='vagrant').backend

    assert vagrant.get_pytest_id() == 'vagrant'


class Test__VagrantBackend__status_method(object):

    def _method_called_counter(self, fn):
        def wrapper(*args, **kwargs):
            wrapper.called += 1
            return fn(*args, **kwargs)
        wrapper.called = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    def create_vagrant_status_output(self, box_data=[]):
        if not box_data:
            create_boxes = [
                dict(box='default-master', box_state='poweroff', box_provider='virtualbox'),
                dict(box='default', box_state='not created', box_provider='virtualbox')
            ]

        header = 'Current machine states:\n\n'
        footer = 'This environment represents multiple VMs. The VMs are all listed\n' \
            'above with their current state. For more information about a specific\n' \
            'VM, run `vagrant status NAME`.\n'
        result = [header]

        for box in create_boxes:
            faked = '{}                        {}       ({})\n'.format(
                box['box'],
                box['box_state'],
                box['box_provider']
            )
            result.append(faked)
        result.append(footer)

        return '\n'.join(result)

    @pytest.fixture
    def mocked_status_refresh(self, mock_vagrant_backend):
        faked_vagrant_status = self.create_vagrant_status_output()

        self.vagrant, self.mocked_method = mock_vagrant_backend('run_vagrant', autospec=True, return_value=faked_vagrant_status)
        self.vagrant.expire_status_cache()

        def reset_counter():
            self.vagrant._refresh_status.called = 0

        self.vagrant._refresh_status = self._method_called_counter(self.vagrant._refresh_status)
        reset_counter()
        yield self.vagrant._refresh_status
        reset_counter()
        assert self.vagrant._refresh_status.called == 0

    def test_when_invoked_twice_before_the_status_refresh_interval_expires(self, mocked_status_refresh):
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

    def test_when_invoking_a_second_time_after_the_status_refresh_interval_expires(self, mocked_status_refresh):
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


def test_VagrantBackend__run__will_not_raise_error(mock_vagrant_backend):
    vagrant, mocked_method = mock_vagrant_backend('run_local', autospec=True)

    result = vagrant.run('vagrant status')
    assert result != ''
    assert result is not None

    mocked_method.assert_called_once_with('vagrant status')


def test_VagrantBackend__ssh_config_to_tmpfile__should_return_the_path_to_the_tempfile_with_saved_sshconfig_and_have_the_right_0600_perms(mock_vagrant_backend, build_ssh_config):
    # We mock run_vagrant because ssh_config -> _refresh_ssh_config -> run_vagrant('vagrant ssh_config')
    fake_ssh_config = build_ssh_config(host='default', hostname='127.0.0.1', user='vagrant', port='99999')
    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True, return_value=fake_ssh_config)

    actual_result = vagrant.ssh_config_to_tmpfile
    mocked_method.assert_called_once_with('vagrant ssh-config %s', 'default')

    assert os.path.isfile(actual_result)
    assert os.stat(actual_result).st_mode & int('0o0777', 8) == 384


def test_VagrantBackend__run_box__method_will_call_communiate_with_wrapped_call_to_get_host_with_paramiko_connection_backend(mock_vagrant_backend, build_ssh_config):
    # communicate -> get_host(hostspec, connection=paramiko, ssh_config)
    fake_ssh_config = build_ssh_config(host='default', hostname='127.0.0.1', user='vagrant', port='99999')
    vagrant, mocked_method = mock_vagrant_backend('get_host', autospec=True)
    vagrant._ssh_config = fake_ssh_config

    vagrant.run_box('whoami')

    mocked_method.assert_called_once_with(vagrant.hostspec, connection='paramiko', ssh_config=vagrant.ssh_config_to_tmpfile)


def test_VagrantBackend__suspend__method_invokes_run_vagrant_with__vagrant_suspend_default(mock_vagrant_backend):
    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autspec=True)
    vagrant.suspend

    mocked_method.assert_called_once_with('vagrant suspend default')


def test_VagrantBackend__halt__method_invokes_stop_with__destroy_False(mock_vagrant_backend):
    vagrant, mocked_method = mock_vagrant_backend('_stop', autspec=True)
    vagrant.halt

    mocked_method.assert_called_once_with(destroy=False)


def test_VagrantBackend__destroy__method_invokes_run_vagrant_with__vagrant_destroy_defualt(mock_vagrant_backend):
    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True)

    vagrant.destroy
    mocked_method.assert_called_once_with('vagrant destroy default --force')
