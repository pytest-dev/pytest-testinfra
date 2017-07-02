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
import testinfra

from testinfra.backend.base import CommandResult


def test__has_snapshot__will_invoke__run_vagrant__with_proper_arguments(mock_vagrant_backend):
    host, run_vagrant_mock = mock_vagrant_backend('run_vagrant', autospec=True, return_value='foo\n')

    assert host.has_snapshot('foo')
    run_vagrant_mock.assert_called_once_with('vagrant snapshot list default')


def test__has_box__will_return__True__when_box_in_list_of_boxes():
    mocked_result = {
        'centos/6': dict(box_name='centos/6', box_provider='virtualbox', box_version='0'),
        'centos/7': dict(box_name='centos/7', box_provider='virtualbox', box_version='0'),
    }

    with mock.patch('testinfra.backend.vagrant.VagrantBackend.boxes', new_callable=mock.PropertyMock, return_value=mocked_result):
        host = testinfra.get_host('vagrant://vagrant@default').backend
        assert host.has_box('centos/6')


def test__run__invokes_run_local_with_valid_commandline_argument(mock_vagrant_backend):
    host, run_local_mock = mock_vagrant_backend('run_local', autospec=True)

    host.run('somecommand arg1')
    run_local_mock.assert_called_once_with('somecommand arg1')


def test__run_vagrant__will_raise__AssertionError__when_command_fails_to_run(mock_vagrant_backend):
    mocked_run_result = mock.MagicMock(spec=CommandResult, stdout='', rc=1, stderr='boom dizzle wizzle', command='vagrant status default')
    host, run_mock = mock_vagrant_backend('run', autospec=True, return_value=mocked_run_result)

    with pytest.raises(AssertionError) as exp:
        host.run_vagrant('vagrant status default')

    assert 'Got exit code 1 from command="vagrant status default" result="boom dizzle wizzle"' in str(exp)
    run_mock.assert_called_once_with('vagrant status default')


def test__run_vagrant__will_return_stdout_when_command_runs_without_an_error(mock_vagrant_backend):
    host, run_mock = mock_vagrant_backend('run', autospec=True)
    # our fake return data
    run_mock.return_value.rc = 0
    run_mock.return_value.command = 'vagrant status'
    run_mock.return_value.stdout = '''Current machine states:

    default-master            poweroff (virtualbox)
    default                   running (virtualbox)

    This environment represents multiple VMs. The VMs are all listed
    above with their current state. For more information about a specific
    VM, run `vagrant status NAME`.'''

    actual_result = host.run_vagrant('vagrant status default')
    run_mock.assert_called_once_with('vagrant status default')

    assert actual_result == run_mock.return_value.stdout


def test__run_box__will_invoke_the_paramiko_backend(mock_vagrant_backend, build_ssh_config):
    # we mock 'get_host' because that is what host.communicate invokes, otherwise we would
    # be attempting to mock a property and that makes tests look uglier IMHO.
    host, get_host_mock = mock_vagrant_backend('get_host', autospec=True)

    # use our mocked ssh_config
    ssh_config = build_ssh_config(host='default', hostname='127.0.0.1', user='vagrant', port='48000')
    host._ssh_config = ssh_config

    host.run_box('hello world')
    get_host_mock.assert_called_once_with('vagrant@default', connection='paramiko', ssh_config=host._ssh_config_tmp)
    get_host_mock.return_value.run.assert_called_once_with('hello world')


# property tests
def test__vagrantfile__property_returns_fully_qualified_path_plus_Vagrantfile(mock_vagrant_backend):
    vagrant, run_vagrant_mock = mock_vagrant_backend('run_vagrant', autospec=True)
    vagrant._vagrantfile = '/tmp/somepath'

    assert vagrant.vagrantfile == '/tmp/somepath/Vagrantfile'


def test__box__when_fetched_and_uninitialized_will_return_default(mock_vagrant_backend):
    vagrant, run_vagrant_mock = mock_vagrant_backend('run_vagrant', autospec=True)
    vagrant._box = None

    assert vagrant.box == 'default'


class Test__boxes__property(object):

    @pytest.fixture
    def mocked_boxes_property(self, mock_vagrant_backend):
        self.fake_vagrant_box_list = '''centos/7            (virtualbox, 1704.01)
jhcook/macos-sierra (virtualbox, 10.12.4)
'''
        self.expected_vagrant_box_list = {
            'jhcook/macos-sierra': {
                'box_name': 'jhcook/macos-sierra',
                'box_provider': 'virtualbox',
                'box_version': '10.12.4',
            },
            'centos/7': {
                'box_name': 'centos/7',
                'box_provider': 'virtualbox',
                'box_version': '1704.01',
            }
        }

        def on_call(stdout='', rc=0, stderr=''):
            self.mocked_result = mock.MagicMock(rc=rc, stdout=stdout, stderr=stderr)
            self.vagrant, self.mocked_method = mock_vagrant_backend('run', autospec=True, return_value=self.mocked_result)

        return on_call

    def test__boxes__will_raise_AsserttionError(self, mocked_boxes_property):
        mocked_boxes_property(stderr='some error message', rc=1)
        with pytest.raises(AssertionError) as errm:
            self.vagrant.boxes

        assert 'some error message' in str(errm)

    def test__boxes__will_return_non_empty_dictionary(self, mocked_boxes_property):
        mocked_boxes_property(rc=0, stdout=self.fake_vagrant_box_list, stderr='')

        actual_result = self.vagrant.boxes

        assert isinstance(actual_result, dict)
        assert actual_result != {}
        assert actual_result is not None
        assert actual_result == self.expected_vagrant_box_list


def test__ssh_config_to_json__will_return_non_empty_JSON(mock_vagrant_backend, build_ssh_config):
    # use our mocked ssh_config
    ssh_config = build_ssh_config(host='default', hostname='127.0.0.1', user='vagrant', port='48000')
    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True, return_value=ssh_config)

    actual_result = vagrant.ssh_config_to_json

    assert isinstance(actual_result, dict)
    assert actual_result != {}
    assert actual_result is not None
    assert actual_result['host'] == 'default'
    assert actual_result['hostname'] == '127.0.0.1'
    assert actual_result['user'] == 'vagrant'
    assert actual_result['port'] == '48000'

    mocked_method.assert_called_once_with('vagrant ssh-config %s', 'default')


def test__ssh_config_to_json__will_return_None(mock_vagrant_backend):
    # vagrant.ssh_config_to_json -> vagrant.ssh_config -> vagrant._refresh_ssh_config
    # mock _refresh_ssh_config to return None
    vagrant, mocked_method = mock_vagrant_backend('_refresh_ssh_config', autospec=True)
    vagrant._ssh_config = None

    actual_result = vagrant.ssh_config_to_json

    assert actual_result is None
    mocked_method.assert_called_once_with()


def test__up__will_invoke__vagrant_up_provision(mock_vagrant_backend):
    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True)

    # ensure that "vagrant up default --provision' is invoked
    vagrant._provision = True
    vagrant.up

    mocked_method.assert_any_call('vagrant up %s --provision', 'default')


def test__up__will_invoke__vagrant_up_without_provision_argument(mock_vagrant_backend):
    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True)

    # ensure that "vagrant up default --provision' is invoked
    vagrant._provision = False
    vagrant.up

    mocked_method.assert_any_call('vagrant up %s', 'default')


def test__provision__will_invoke__vagrant_provision(mock_vagrant_backend):
    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True)

    vagrant.provision

    mocked_method.assert_called_once_with('vagrant provision %s', 'default')


class Test__has_vagrantfile__returns_True(object):

    def test__has_vagrantfile__will_return_True_when_vagrantfile_is_a_file_on_disk(self, mock_vagrant_backend):
        # need to mock something so run_vagrant was choosen, but is not used.
        vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True)

        with mock.patch('os.path.basename', autospec=False, return_value='foo') as mocked_method:
            with mock.patch('os.path.isfile', autospec=True, return_value=True) as is_file_mock:
                vagrant.has_vagrantfile
                is_file_mock.assert_called_once_with(vagrant.vagrantfile)

        mocked_method.assert_any_call(vagrant.vagrantfile.strip('/Vagrantfile'))

    def test__has_vagrantfile__will_return_True_when_current_pwd_is_inside_vagrant_directory(self, mock_vagrant_backend):
        vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True)

        expected_pwd = os.getcwd()
        with mock.patch('os.path.basename', autospec=True, return_value='foo') as mocked_method:
            # we also mock out os.path.isfile = False to make sure we are isolating our test
            with mock.patch('os.path.isfile', autospec=True, return_value=False) as is_file_mock:
                actual_result = vagrant.has_vagrantfile
                vagrant_dir = vagrant.vagrantfile.strip('/Vagrantfile')

                mocked_method.assert_any_call(expected_pwd)
                mocked_method.assert_any_call(vagrant_dir)
                is_file_mock.assert_called_once_with(vagrant.vagrantfile)
                assert actual_result is True
                assert os.path.isfile(vagrant.vagrantfile) is False


def test__stop__will_only_invoke__vagrant_destroy_force(mock_vagrant_backend):
    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True)

    vagrant._stop(destroy=True)

    mocked_method.assert_called_once_with('vagrant destroy --force default')


def test__stop__will_only_invoke__vagrant_destroy_halt(mock_vagrant_backend):
    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True)

    vagrant._stop(destroy=False)

    mocked_method.assert_called_once_with('vagrant halt --force default')


def test__validate_requirements__will_raise__RuntimeError__that_explains_vagrant_must_be_installed(mock_vagrant_backend):
    # vagrant._validate_requirements -> self.has_vagrant -> self.run_local
    vagrant, mocked_method = mock_vagrant_backend('run_local', autospec=True, rc=1)

    vagrant.setting['VALIDATE_HAS_VAGRANT'] = True

    with pytest.raises(RuntimeError) as errm:
        vagrant._validate_requirements()

    assert 'Vagrant must be installed' in str(errm)


def test__validate_requirements__will_raise__RuntimeError__that_explains_vagrantfile_cannot_be_found_on_disk(mock_vagrant_backend):
    # vagrant._validate_requirements -> self.has_vagrant -> self.run_local
    vagrant, mocked_method = mock_vagrant_backend('run_local', autospec=True, rc=0)

    # ensure that we don't trigger the 'has_vagrant' check
    vagrant.setting['VALIDATE_HAS_VAGRANT'] = False
    vagrant._vagrantfile = '/some/path/dne'

    # mock vagrant.has_vagrantfile -> False
    type(vagrant).has_vagrantfile = mock.PropertyMock(return_value=False)

    with pytest.raises(RuntimeError) as errm:
        vagrant._validate_requirements()

    assert 'Unable to find Vagrantfile' in str(errm)


@pytest.mark.parametrize(
    'state,is_running',
    [
        ('aborted', False),
        ('not created', False),
        ('paused', False),
        ('poweroff', False),
        ('saved', False),
        ('suspended', False),
        ('not running', False),
    ]
)
def test__refresh_status__when_non_running_state_should_return__is_running__eq_to__False(state, is_running, mock_vagrant_backend):
    fake_vagrant_status = """Current machine states:

default                   {} (virtualbox)

To resume this VM, simply run `vagrant up`.
    """.format(state)

    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True, return_value=fake_vagrant_status)
    vagrant.setting['VALIDATE_HAS_VAGRANT'] = False

    actual_result = vagrant._refresh_status()

    assert actual_result.is_running is is_running, (
        'Expected result to be "{}" when vagrant status reports "{}"'
    ).format(is_running, state)


@pytest.mark.parametrize(
    'state,is_running',
    [
        ('running', True),
    ]
)
def test__refresh_status__when_in_running_state_should_return__is_running__eq_to__True(state, is_running, mock_vagrant_backend):
    fake_vagrant_status = """Current machine states:

default                   {} (virtualbox)

To resume this VM, simply run `vagrant up`.
    """.format(state)

    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True, return_value=fake_vagrant_status)
    vagrant.setting['VALIDATE_HAS_VAGRANT'] = False

    actual_result = vagrant._refresh_status()

    assert actual_result.is_running is is_running, (
        'Expected result to be "{}" when vagrant status reports "{}"'
    ).format(is_running, state)


@pytest.mark.parametrize(
    'state,is_running',
    [
        ('foobazzle', None),
    ]
)
def test__refresh_status__should_raise__NotImplementedError__when_status_is_not_implemented(state, is_running, mock_vagrant_backend):
    fake_vagrant_status = """Current machine states:

default                   {} (virtualbox)

To resume this VM, simply run `vagrant up`.
    """.format(state)

    vagrant, mocked_method = mock_vagrant_backend('run_vagrant', autospec=True, return_value=fake_vagrant_status)
    vagrant.setting['VALIDATE_HAS_VAGRANT'] = False

    with pytest.raises(NotImplementedError) as errm:
        actual_result = vagrant._refresh_status()

        assert actual_result.is_running is is_running, (
            'Expected result to be "{}" when vagrant status reports "{}"'
        ).format(is_running, state)

    expected_errm = (
        'un-handled status from `vagrant status {}` got "{}"'
    ).format(vagrant.box, state)

    assert expected_errm in str(errm)
