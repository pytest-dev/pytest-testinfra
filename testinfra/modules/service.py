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

from testinfra.modules.base import Module
from testinfra.utils import cached_property


class Service(Module):
    """Test services

    Implementations:

    - Linux: detect Systemd, Upstart or OpenRC, fallback to SysV
    - FreeBSD: service(1)
    - OpenBSD: ``/etc/rc.d/$name check`` for ``is_running``
      ``rcctl ls on`` for ``is_enabled`` (only OpenBSD >= 5.8)
    - NetBSD: ``/etc/rc.d/$name onestatus`` for ``is_running``
      (``is_enabled`` is not yet implemented)

    """

    def __init__(self, name):
        self.name = name
        super(Service, self).__init__()

    @property
    def is_running(self):
        """Test if service is running"""
        raise NotImplementedError

    @property
    def is_enabled(self):
        """Test if service is enabled"""
        raise NotImplementedError

    # pylint: disable=too-many-return-statements
    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            if (
                host.exists("systemctl")
                and "systemd" in host.file("/sbin/init").linked_to
            ):
                return SystemdService
            elif (host.exists("initctl")
                    and host.exists('status')
                    and host.file('/etc/init').is_directory):
                return UpstartService
            elif host.exists("rc-service"):
                return OpenRCService
            return SysvService
        elif host.system_info.type == "freebsd":
            return FreeBSDService
        elif host.system_info.type == "openbsd":
            return OpenBSDService
        elif host.system_info.type == "netbsd":
            return NetBSDService
        raise NotImplementedError

    def __repr__(self):
        return "<service %s>" % (self.name,)


class SysvService(Service):

    @cached_property
    def _service_command(self):
        return self._find_command('service')

    @property
    def is_running(self):
        # based on /lib/lsb/init-functions
        # 0: program running
        # 1: program is dead and pid file exists
        # 3: not running and pid file does not exists
        # 4: Unable to determine status
        return self.run_expect(
            [0, 1, 3], "%s %s status",
            self._service_command, self.name).rc == 0

    @property
    def is_enabled(self):
        return bool(self.check_output(
            "find /etc/rc?.d/ -name %s",
            "S??" + self.name,
        ))


class SystemdService(SysvService):

    @property
    def is_running(self):
        return self.run_expect(
            [0, 3], "systemctl is-active %s", self.name).rc == 0

    @property
    def is_enabled(self):
        cmd = self.run_test("systemctl is-enabled %s", self.name)
        if cmd.rc == 0:
            return True
        elif cmd.stdout.strip() == "disabled":
            return False
        # Fallback on SysV
        # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=760616
        return super(SystemdService, self).is_enabled

    @property
    def is_valid(self):
        # systemd-analyze requires a full path.
        if self.name.endswith(".service"):
            name = self.name
        else:
            name = self.name + ".service"
        cmd = self.run("systemd-analyze verify %s", name)
        # A bad unit file still returns a rc of 0, so check the
        # stdout for anything.  Nothing means no warns/errors.
        # Docs at https://www.freedesktop.org/software/systemd/man/systemd
        # -analyze.html#Examples%20for%20verify
        assert (cmd.stdout, cmd.stderr) == ("", "")
        return True


class UpstartService(SysvService):

    @property
    def is_enabled(self):
        if self.run(
            "grep -q '^start on' /etc/init/%s.conf",
            self.name,
        ).rc == 0 and self.run(
            "grep -q '^manual' /etc/init/%s.override",
            self.name,
        ).rc != 0:
            return True
        # Fallback on SysV
        return super(UpstartService, self).is_enabled

    @property
    def is_running(self):
        cmd = self.run_test('status %s', self.name)
        if cmd.rc == 0 and len(cmd.stdout.split()) > 1:
            return 'running' in cmd.stdout.split()[1]
        return super(UpstartService, self).is_running


class OpenRCService(SysvService):

    @cached_property
    def _service_command(self):
        return self._find_command("rc-service")

    @property
    def is_enabled(self):
        return bool(self.check_output(
            "find /etc/runlevels/ -name %s",
            self.name,
        ))


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

    @property
    def is_enabled(self):
        if self.name in self.check_output('rcctl ls on').splitlines():
            return True
        if self.name in self.check_output('rcctl ls off').splitlines():
            return False
        raise RuntimeError(
            "Unable to determine state of {0}. Does this service exist?"
            .format(self.name))


class NetBSDService(Service):

    @property
    def is_running(self):
        return self.run_test("/etc/rc.d/%s onestatus", self.name).rc == 0

    @property
    def is_enabled(self):
        raise NotImplementedError
