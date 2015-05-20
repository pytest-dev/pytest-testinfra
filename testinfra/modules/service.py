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

import pytest

from testinfra.modules.base import Module


class Service(Module):
    """Test services"""

    def __init__(self, name):
        self.name = name
        super(Service, self).__init__()

    @property
    def is_running(self):
        """Check if service is running"""
        raise NotImplementedError

    @property
    def is_enabled(self):
        """Check if service is enabled"""
        raise NotImplementedError

    @classmethod
    def as_fixture(cls):
        @pytest.fixture(scope="module")
        def f(SystemInfo, Command, File):
            if SystemInfo.type == "linux":
                if (
                    Command.run_test("which systemctl").rc == 0
                    and "systemd" in File("/sbin/init").linked_to
                ):
                    return SystemdService
                else:
                    return LinuxService
            elif SystemInfo.type == "freebsd":
                return FreeBSDService
            elif SystemInfo.type == "openbsd":
                return OpenBSDService
            elif SystemInfo.type == "netbsd":
                return NetBSDService
            else:
                raise NotImplementedError
        f.__doc__ = cls.__doc__
        return f

    def __repr__(self):
        return "<service %s>" % (self.name,)


class LinuxService(Service):

    @property
    def is_running(self):
        # based on /lib/lsb/init-functions
        # 0: program running
        # 1: program is dead and pid file exists
        # 3: not running and pid file does not exists
        # 4: Unable to determine status
        return self.run_expect(
            [0, 1, 3], "service %s status", self.name).rc == 0

    @property
    def is_enabled(self):
        return self.is_enabled_with_level(3)

    def is_enabled_with_level(self, level):
        # sysv
        if self.run_test(
            "ls /etc/rc%s.d | grep -q 'S..%s'",
            str(level), self.name
        ).rc == 0:
            return True
        # systemd
        elif self.run(
            "grep -q 'start on' /etc/init/%s.conf", self.name
        ).rc == 0:
            return True
        else:
            return False


class SystemdService(Service):

    @property
    def is_running(self):
        return self.run_expect(
            [0, 3], "systemctl is-active %s", self.name).rc == 0

    @property
    def is_enabled(self):
        return self.run_test("systemctl is-enabled %s", self.name).rc == 0


class FreeBSDService(Service):

    @property
    def is_running(self):
        return self.run_test("service %s onestatus", self.name).rc == 0

    @property
    def is_enabled(self):
        # Return list of enabled services like
        # /etc/rc.d/sshd
        # /etc/rc.d/sendmail
        for path in self.check_output("service -e").splitlines():
            if path and path.rsplit("/", 1)[1] == self.name:
                return True
        return False


class OpenBSDService(Service):

    @property
    def is_running(self):
        return self.run_test("/etc/rc.d/%s check", self.name).rc == 0


class NetBSDService(Service):

    @property
    def is_running(self):
        return self.run_test("/etc/rc.d/%s onestatus", self.name).rc == 0
