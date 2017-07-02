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
from contextlib import contextmanager

import logging
import os
import re
import tempfile
import time

from testinfra.backend import base

logger = logging.getLogger("testinfra")

BACKEND = 'VagrantBackend'


@contextmanager
def run_command_in_directory(path):
    path = os.path.dirname(path)
    orig_dir = os.getcwd()
    try:
        if os.path.basename(orig_dir) != os.path.basename(path):
            os.chdir(path)
        logger.debug(BACKEND + ' In directory %s', os.getcwd())
        yield
    finally:
        # always change our directory back
        os.chdir(orig_dir)
        logger.debug(BACKEND + ' Changed directory back to %s', orig_dir)


class VagrantBackend(base.BaseBackend):  # pylint: disable=R0902,R0904
    NAME = "vagrant"

    def __init__(self, hostspec=None, user='vagrant', vagrantfile='./Vagrantfile', box='default', provision=None, status_refresh_interval=15, *args, **kwargs):
        if hostspec:
            box, user, _ = self.parse_hostspec(hostspec)
        super(VagrantBackend, self).__init__(hostname=box, *args, **kwargs)
        self._user = (user or 'vagrant')
        self._vagrantfile = vagrantfile
        self._box = box
        self._status = None
        self._status_refresh_interval = None
        self._last_refreshed = None
        self.setting = dict(VALIDATE_HAS_VAGRANT=True)
        self._ssh_config = None
        self._ssh_config_tmp = None
        self.status_refresh_interval = status_refresh_interval
        self._provision = provision

    def __call__(self, *args, **kwargs):
        return VagrantBackend(*args, **kwargs)

    @classmethod
    def get_hosts(cls, host, **kwargs):
        return [host]

    def get_pytest_id(self):
        return 'vagrant'

    def has_snapshot(self, snapshot_name):
        snapshot_cmd = 'vagrant snapshot list {}'.format(self.box)
        snapshots = self.run_vagrant(snapshot_cmd).split('\n')
        return snapshot_name in snapshots

    def has_box(self, box_name):
        return box_name in self.boxes

    def run(self, command, *args, **kwargs):
        cmd = self.get_command(command, *args)
        return self.run_local(cmd, **kwargs)

    def run_vagrant(self, command, *args, **kwargs):
        self._validate_requirements()

        with run_command_in_directory(self.vagrantfile):
            out = self.run(command, *args, **kwargs)
            stderr = out.stderr.rstrip('\r\n').rstrip('\n')
            stdout = out.stdout.rstrip('\r\n').rstrip('\n')
            err_msg = 'Got exit code %s from command="%s" result="%s"' \
                % (out.rc, out.command, stderr)
            assert out.rc == 0, err_msg
            return stdout

    def run_box(self, command, *args, **kwargs):
        box = self.communicate
        result = box.run(command, *args, **kwargs)
        return result

    def expire_status_cache(self):
        self._last_refreshed = None
        self._ssh_config = None

    @property
    def vagrantfile(self):
        if not self._vagrantfile.endswith('Vagrantfile'):
            self._vagrantfile += '/Vagrantfile'
        return self._vagrantfile

    @property
    def box(self):
        if not self._box:
            self._box = 'default'
        return self._box

    @property
    def boxes(self):
        out = self.run('vagrant box list')
        stderr = out.stderr.rstrip('\r\n').rstrip('\n')
        err_msg = 'Unable to get vagrant box list, ' + \
                  'got stderr="{}"'.format(stderr)
        assert out.rc == 0, err_msg

        my_boxes = re.sub('\r\n$|\n$', '\n', out.stdout).rstrip()
        my_boxes = re.split('\n', my_boxes)

        results = {}

        for my_box in my_boxes:
            my_box = re.sub(r'[(),]', '', my_box)
            my_box = re.sub(r'\s\s+', ' ', my_box)

            bname, bprovider, bver = my_box.split(' ')

            results[bname] = dict(box_name=bname, box_provider=bprovider,
                                  box_version=bver)

        return results

    @property
    def user(self):
        return self._user

    @property
    def hostspec(self):
        return self.user + '@' + self.box

    @property
    def status(self):
        if self.should_refresh_status:
            return self._refresh_status()
        return self._status

    @property
    def status_refresh_interval(self):
        return self._status_refresh_interval

    @status_refresh_interval.setter
    def status_refresh_interval(self, val):
        self._status_refresh_interval = val
        self.expire_status_cache()

    @property
    def ssh_config(self):
        self._refresh_ssh_config()
        return self._ssh_config

    @property
    def ssh_config_to_tmpfile(self):
        if self._ssh_config_tmp is None:
            self._ssh_config_tmp = tempfile.NamedTemporaryFile(delete=False).name

        os.chmod(self._ssh_config_tmp, 384)  # oct 0600
        with open(self._ssh_config_tmp, 'wb') as fd:
            fd.write(self.ssh_config.encode('utf-8'))

        return self._ssh_config_tmp

    @property
    def ssh_config_to_json(self):
        out = self.ssh_config
        if out:
            def create_regex_group(s):
                lines = (line.strip() for line in s.split('\n') if line.strip())
                chars = filter(None,
                               (line.split('#')[0].strip()
                                for line in lines)
                               )
                return re.compile(r''.join(chars)).search(out)
            match = create_regex_group(
                r'''Host\s+(?P<host>.*)
                \s*HostName\s+(?P<hostname>.*)
                \s*User\s+(?P<user>.*)
                \s*Port\s+(?P<port>\d+)
                \s*UserKnownHostsFile\s+(?P<user_known_hosts_file>.*)
                \s*StrictHostKeyChecking\s+(?P<strict_host_key_checking>.*)
                \s*PasswordAuthentication\s+(?P<password_authentication>.*)
                \s*IdentityFile\s+(?P<identity_file>.*)
                \s*IdentitiesOnly\s+(?P<identities_only>.*)
                \s*LogLevel\s+(?P<log_level>.*)'''
            )
            return match.groupdict() if match else None

    @property
    def communicate(self):
        ssh = self.get_host(self.hostspec, connection='paramiko', ssh_config=self.ssh_config_to_tmpfile)
        return ssh

    @property
    def up(self):
        if self._provision:
            out = self.run_vagrant('vagrant up %s --provision', self.box)
        else:
            out = self.run_vagrant('vagrant up %s', self.box)
        self.expire_status_cache()
        self._refresh_ssh_config()
        return out

    @property
    def halt(self):
        self.expire_status_cache()
        return self._stop(destroy=False)

    @property
    def destroy(self):
        self.expire_status_cache()
        return self._stop(destroy=True)

    @property
    def suspend(self):
        self.expire_status_cache()
        suspend_cmd = 'vagrant suspend ' + self.box
        return self.run_vagrant(suspend_cmd)

    @property
    def provision(self):
        out = self.run_vagrant('vagrant provision %s', self.box)
        return out

    @property
    def has_vagrant(self):
        return self.run_local('type vagrant').rc == 0

    @property
    def has_vagrantfile(self):
        pwd = os.path.basename(os.getcwd())
        vagrant_dir = os.path.basename(self.vagrantfile.strip('/Vagrantfile'))
        my_pwd_is_inside_vagrant_dir = vagrant_dir == pwd
        return os.path.isfile(self.vagrantfile) or my_pwd_is_inside_vagrant_dir

    @property
    def should_refresh_status(self):
        if self._last_refreshed is None:
            self._last_refreshed = time.time() - self.status_refresh_interval
        time_between_last_run = round(time.time() - self._last_refreshed, 2)

        should_refresh = time_between_last_run >= self.status_refresh_interval
        return should_refresh

    def _stop(self, destroy=False):
        run_args = ['vagrant']
        if destroy:
            run_args.append('destroy')
        else:
            run_args.append('halt')
        run_args.append('--force')
        run_args.append(self.box)
        run_args = ' '.join(run_args)
        out = self.run_vagrant(run_args)
        return out

    def _validate_requirements(self):
        if not self.has_vagrant and self.setting.get('VALIDATE_HAS_VAGRANT', True):
            raise RuntimeError('Vagrant must be installed in order ' +
                               'to use this fixture')

        if not self.has_vagrantfile:
            raise RuntimeError(
                'Unable to find Vagrantfile "{}" and I am in directory {}'.format(
                    self.vagrantfile,
                    os.getcwd()
                )
            )

    def _refresh_status(self):
        out = self.run_vagrant('vagrant status %s', self.box)
        status = re.sub(r'  +| \(', '|', out).rstrip(')').split('|')[1]

        # update the counter that controls this cache
        self._last_refreshed = time.time()

        if status in ('aborted', 'not created', 'paused', 'poweroff', 'saved',
                      'suspended', 'not running'):
            as_running = False
            as_not_running = True
            created = status != 'not created'
        elif status == 'running':
            as_running = True
            as_not_running = False
            created = True
        else:
            raise NotImplementedError('This is a bug, un-handled status from ' +
                                      '`vagrant status {}` '.format(self.box) +
                                      'got "{}"'.format(status)
                                      )

        def cmd():
            def add(key, val):
                setattr(cmd, key, val)
            cmd.add = add
            return cmd

        cmd = cmd()
        cmd.add('to_be_running', as_running)
        cmd.add('not_to_be_running', as_not_running)
        cmd.add('is_running', as_running)
        cmd.add('is_not_running', as_not_running)
        cmd.add('running', as_running)
        cmd.add('not_running', as_not_running)
        cmd.add('is_created', created)
        cmd.add('is_not_created', not created)

        self._status = cmd
        return self._status

    def _refresh_ssh_config(self):
        if self._ssh_config is None:
            self._ssh_config = self.run_vagrant('vagrant ssh-config %s',
                                                self.box
                                                )
