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
    "%s://centos_7" % (b_type,)
    for b_type in ("ssh", "paramiko", "safe-ssh")
] + ["docker://" + DockerComposeService.get("centos_7")["name"]]

if sys.version_info == 2:
    testinfra_hosts.append("ansible://centos_7")


def test_ssh_package(Package):
    ssh = Package("openssh-server")
    assert ssh.is_installed
    assert ssh.version.startswith("6.6")


def test_ssh_service(Service):
    ssh = Service("sshd")
    assert ssh.is_running
    assert ssh.is_enabled


def test_systeminfo(SystemInfo):
    assert SystemInfo.type == "linux"
    assert SystemInfo.release == "7"
    assert SystemInfo.distribution == "centos"
    assert SystemInfo.codename is None


def test_process(Process):
    systemd = Process.get(pid=1)
    assert systemd.ppid == 0
    assert systemd.args == "/usr/sbin/init"
    assert systemd.comm == "systemd"
    assert systemd.euid == 0
