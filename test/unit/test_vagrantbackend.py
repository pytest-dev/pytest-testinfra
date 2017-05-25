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
import pytest
import testinfra


def test__has_snapshot__will_invoke__run_vagrant__with_proper_arguments():
    with mock.patch('testinfra.backend.vagrant.VagrantBackend.run_vagrant', autospec=True, return_value='foo\n') as m:
        host = testinfra.get_host('vagrant://vagrant@default').backend
        assert host.has_snapshot('foo')
        m.assert_called_once_with(host, 'vagrant snapshot list default')


def test__has_box__will_return__True__when_box_in_list_of_boxes():

    mocked_result = {
        'centos/6': dict(box_name='centos/6', box_provider='virtualbox', box_version='0'),
        'centos/7': dict(box_name='centos/7', box_provider='virtualbox', box_version='0'),
    }

    with mock.patch('testinfra.backend.vagrant.VagrantBackend.boxes', new_callable=mock.PropertyMock, return_value=mocked_result):
        host = testinfra.get_host('vagrant://vagrant@default').backend
        assert host.has_box('centos/6')


def test__run_vagrant__will_raise__AssertionError__when_command_fails_to_run(tmpdir):
    vbox_dir = tmpdir.join('Vagrantfile')
    vbox_dir.write('foo')

    with mock.patch('testinfra.backend.vagrant.VagrantBackend.run', autospec=True) as m:
        host = testinfra.get_host('vagrant://vagrant@default', vagrantfile=str(vbox_dir)).backend

        # our fake return data
        m.return_value.rc = 1
        m.return_value.command = 'vagrant status'
        m.return_value.stderr = 'boom dizzle wizzle'

        with pytest.raises(AssertionError) as exp:
            host.run_vagrant('vagrant status default')

        assert 'Got exit code 1 from command="vagrant status" result="boom dizzle wizzle"' in str(exp)
        m.assert_called_once_with(host, 'vagrant status default')


def test__run_vagrant__will_return_stdout_when_command_runs_without_an_error(tmpdir):
    vbox_dir = tmpdir.join('Vagrantfile')
    vbox_dir.write('foo')

    with mock.patch('testinfra.backend.vagrant.VagrantBackend.run', autospec=True) as m:
        host = testinfra.get_host('vagrant://vagrant@default', vagrantfile=str(vbox_dir)).backend

        # our fake return data
        m.return_value.rc = 0
        m.return_value.command = 'vagrant status'
        m.return_value.stdout = '''Current machine states:

        default-master            poweroff (virtualbox)
        default                   running (virtualbox)

        This environment represents multiple VMs. The VMs are all listed
        above with their current state. For more information about a specific
        VM, run `vagrant status NAME`.'''

        actual_result = host.run_vagrant('vagrant status default')
        m.assert_called_once_with(host, 'vagrant status default')

        assert actual_result == m.return_value.stdout


def test__run_box__will_invoke_the_paramiko_backend(tmpdir, build_ssh_config):

    vbox_dir = tmpdir.join('Vagrantfile')
    vbox_dir.write('')

    host = testinfra.get_host('vagrant://vagrant@default', vagrantfile=str(vbox_dir)).backend

    # use our mocked ssh_config
    ssh_config = build_ssh_config(host='default', hostname='127.0.0.1', user='vagrant', port='48000')
    host._ssh_config = ssh_config

    with mock.patch.object(host, 'get_host', autospec=True) as m:
        host.run_box('hello world')
        m.assert_called_once_with('vagrant@default', connection='paramiko', ssh_config=host._ssh_config_tmp)
        m.return_value.run.assert_called_once_with('hello world')
