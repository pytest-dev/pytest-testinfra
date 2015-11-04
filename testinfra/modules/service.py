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

from testinfra.modules.base import Module


class Service(Module):
    """Test services"""

    def __init__(self, _backend, name):
        self.name = name
        super(Service, self).__init__(_backend)

    def __call__(self, name):
        return self.__class__(self._backend, name)

    @property
    def is_running(self):
        """Check if service is running"""
        raise NotImplementedError

    @property
    def is_enabled(self):
        """Check if service is enabled"""
        raise NotImplementedError

    @classmethod
    def get_module(cls, _backend):
        SystemInfo = _backend.get_module("SystemInfo")
        if SystemInfo.type == "linux":
            return LinuxService(_backend, None)
        elif SystemInfo.type == "freebsd":
            return FreeBSDService(_backend, None)
        elif SystemInfo.type == "openbsd":
            return OpenBSDService(_backend, None)
        elif SystemInfo.type == "netbsd":
            return NetBSDService(_backend, None)
        else:
            raise NotImplementedError

    def __repr__(self):
        return "<service %s>" % (self.name,)


class LinuxService(Service):
    SYSTEMD, UPSTART, SYSV = range(3)

    def __init__(self, backend, name):
        self._service_backend = None
        super(LinuxService, self).__init__(backend, name)

    @property
    def service_backend(self):
        File = self._backend.get_module("File")
        if self._service_backend is None:
            if (
                self.run_test("which systemctl").rc == 0
                and "systemd" in File("/sbin/init").linked_to
            ):
                self._service_backend = self.SYSTEMD
            elif self.run_test("which initctl").rc == 0:
                self._service_backend = self.UPSTART
            else:
                self._service_backend = self.SYSV
        return self._service_backend

    @property
    def is_running(self):
        if self.service_backend == self.SYSTEMD:
            return self.run_expect(
                [0, 3], "systemctl is-active %s", self.name).rc == 0
        else:
            # based on /lib/lsb/init-functions
            # 0: program running
            # 1: program is dead and pid file exists
            # 3: not running and pid file does not exists
            # 4: Unable to determine status
            return self.run_expect(
                [0, 1, 3], "service %s status", self.name).rc == 0

    @property
    def is_enabled(self):
        if self.service_backend == self.SYSTEMD:
            cmd = self.run_test("systemctl is-enabled %s", self.name)
            if cmd.rc == 0:
                return True
            elif cmd.stdout.strip() == "disabled":
                return False
        elif self.service_backend == self.UPSTART:
            if self.run(
                "grep -q '^start on' /etc/init/%s.conf",
                self.name,
            ).rc == 0 and self.run(
                "grep -q '^manual' /etc/init/%s.override",
                self.name,
            ).rc != 0:
                return True

        # SysV
        # Fallback for both systemd and upstart while distro mix them with sysv
        # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=760616
        if self.check_output(
            "find /etc/rc?.d -name %s",
            "S??" + self.name,
        ):
            return True

        return False


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
