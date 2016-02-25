# -*- coding: utf8 -*-
# Copyright © 2015 Philippe Pepiot
#
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

import sys

import pytest

from testinfra.utils.docker_compose_to_ssh_config import DockerComposeService

pytestmark = pytest.mark.integration
testinfra_hosts = [
    "%s://debian_wheezy" % (b_type,)
    for b_type in ("ssh", "paramiko", "safe-ssh")
] + ["docker://" + DockerComposeService.get("debian_wheezy")["name"]]

if sys.version_info[0] == 2:
    testinfra_hosts.append("ansible://debian_wheezy")


def test_ssh_package(Package):
    ssh = Package("openssh-server")
    assert ssh.is_installed
    assert ssh.version.startswith("1:6.0p1")


def test_ssh_service(Service):
    ssh = Service("ssh")
    assert ssh.is_running
    assert ssh.is_enabled


def test_systeminfo(SystemInfo):
    assert SystemInfo.type == "linux"
    assert SystemInfo.release == "7"
    assert SystemInfo.distribution == "debian"
    assert SystemInfo.codename is None


def test_user(User):
    user = User("sshd")
    assert user.exists
    assert user.name == "sshd"
    assert user.uid == 101
    assert user.gid == 65534
    assert user.group == "nogroup"
    assert user.gids == [65534]
    assert user.groups == ["nogroup"]
    assert user.shell == "/usr/sbin/nologin"
    assert user.home == "/var/run/sshd"


def test_nonexistent_user(User):
    assert not User("zzzzzzzzzz").exists


def test_current_user(User):
    assert User().name == "root"


def test_group(Group):
    assert Group("root").exists
    assert Group("root").gid == 0


def test_process(Process):
    ssh = Process.get(pid=1)
    assert ssh.ppid == 0
    assert ssh.args == "/usr/sbin/sshd -D"
    assert ssh.comm == "sshd"
    assert ssh.euid == 0
