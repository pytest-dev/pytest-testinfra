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


@pytest.fixture
def mock_vagrant_backend(request, monkeypatch, tmpdir):
    def on_call(method, hostspec='vagrant@default', vagrantfile='./Vagrantfile', *args, **kwargs):

        my_tmpdir = tmpdir.join('Vagrantfile')
        content = """

Vagrant.configure("2") do |config|
  config.vm.box = "centos/7"
end

"""
        vagrantfile = str(my_tmpdir)
        if os.path.isfile(vagrantfile):
            with open(vagrantfile, 'r') as fd:
                content = fd.read()

        my_tmpdir.write(content)
        host = testinfra.get_host(hostspec, connection='vagrant', vagrantfile=vagrantfile).backend

        def mocked_has_vagrant(*args):
            # simulate self.run_local('type vagrant').rc == 0
            if 'type vagrant' in args:
                mocked_result = mock.MagicMock(spec=CommandResult, rc=0)
                mocked_result.return_value.rc = 0
                return mocked_result
            return mock.MagicMock(spec=CommandResult)

        monkeypatch.setattr(host, 'run_local', mocked_has_vagrant)

        patcher = mock.patch.object(host, method, **kwargs)
        mocked_method = patcher.start()

        def teardown():
            teardown.patcher.stop()

        teardown.patcher = patcher
        teardown.mocked_method = mocked_method

        # add teardown when fixture goes out of scope
        request.addfinalizer(teardown)

        return host, mocked_method

    return on_call


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


def test__run_vagrant__will_raise__AssertionError__when_command_fails_to_run(mock_vagrant_backend):
    mocked_run_result = mock.MagicMock(spec=CommandResult, stdout='', rc=1, stderr='boom dizzle wizzle', command='vagrant status default')
    host, run_mock = mock_vagrant_backend('run', autospec=True, return_value=mocked_run_result)

    with pytest.raises(AssertionError) as exp:
        host.run_vagrant('vagrant status default')

    assert 'Got exit code 1 from command="vagrant status default" result="boom dizzle wizzle"' in str(exp)
    run_mock.assert_called_once_with('vagrant status default')


def test__run__invokes_run_local_with_valid_commandline_argument(mock_vagrant_backend):
    host, run_local_mock = mock_vagrant_backend('run_local', autospec=True)

    host.run('somecommand arg1')
    run_local_mock.assert_called_once_with('somecommand arg1')


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
