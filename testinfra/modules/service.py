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

import functools

from testinfra.modules.base import Module


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
        super().__init__()

    @property
    def exists(self):
        """Test if service is exists"""
        raise NotImplementedError

    @property
    def is_running(self):
        """Test if service is running"""
        raise NotImplementedError

    @property
    def is_enabled(self):
        """Test if service is enabled"""
        raise NotImplementedError

    @property
    def is_valid(self):
        """Test if service is valid

        This method is only available in the systemd implementation,
        it will raise ``NotImplementedError`` in others implementation
        """
        raise NotImplementedError

    @property
    def is_masked(self):
        """Test if service is masked

        This method is only available in the systemd implementation,
        it will raise ``NotImplementedError`` in others implementations
        """
        raise NotImplementedError

    @functools.cached_property
    def systemd_properties(self):
        """Properties of the service (unit).

        Return service properties as a `dict`,
        empty properties are not returned.

        >>> ntp = host.service("ntp")
        >>> ntp.systemd_properties["FragmentPath"]
        '/lib/systemd/system/ntp.service'

        This method is only available in the systemd implementation,
        it will raise ``NotImplementedError`` in others implementations

        Note: based on `systemctl show`_

        .. _systemctl show: https://man7.org/linux/man-pages/man1/systemctl.1.html
        """
        raise NotImplementedError

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            if host.file("/run/systemd/system/").is_directory or (
                host.exists("systemctl")
                and "systemd" in host.file("/sbin/init").linked_to
            ):
                return SystemdService
            if (
                host.exists("initctl")
                and host.exists("status")
                and host.file("/etc/init").is_directory
            ):
                return UpstartService
            if host.exists("rc-service"):
                return OpenRCService
            return SysvService
        if host.system_info.type == "freebsd":
            return FreeBSDService
        if host.system_info.type == "openbsd":
            return OpenBSDService
        if host.system_info.type == "netbsd":
            return NetBSDService
        if host.system_info.type == "windows":
            return WindowsService
        raise NotImplementedError

    def __repr__(self):
        return "<service {}>".format(self.name)


class SysvService(Service):
    @functools.cached_property
    def _service_command(self):
        return self.find_command("service")

    @property
    def is_running(self):
        # based on /lib/lsb/init-functions
        # 0: program running
        # 1: program is dead and pid file exists
        # 3: not running and pid file does not exists
        # 4: Unable to determine status
        # 8: starting (alpine specific ?)
        return (
            self.run_expect(
                [0, 1, 3, 8], "%s %s status", self._service_command, self.name
            ).rc
            == 0
        )

    @property
    def is_enabled(self):
        return bool(
            self.check_output(
                "find -L /etc/rc?.d/ -name %s",
                "S??" + self.name,
            )
        )


class SystemdService(SysvService):
    suffix_list = [
        "service",
        "socket",
        "device",
        "mount",
        "automount",
        "swap",
        "target",
        "path",
        "timer",
        "slice",
        "scope",
    ]
    """
    List of valid suffixes for systemd unit files

    See systemd.unit(5) for more details
    """

    def _has_systemd_suffix(self):
        """
        Check if service name has a known systemd unit suffix
        """
        unit_suffix = self.name.split(".")[-1]
        return unit_suffix in self.suffix_list

    @property
    def exists(self):
        cmd = self.run_test('systemctl list-unit-files | grep -q "^%s"', self.name)
        return cmd.rc == 0

    @property
    def is_running(self):
        out = self.run_expect([0, 1, 3], "systemctl is-active %s", self.name)
        if out.rc == 1:
            # Failed to connect to bus: No such file or directory
            return super().is_running
        return out.rc == 0

    @property
    def is_enabled(self):
        cmd = self.run_test("systemctl is-enabled %s", self.name)
        if cmd.rc == 0:
            return True
        if cmd.stdout.strip() == "disabled":
            return False
        # Fallback on SysV - only for non-systemd units
        # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=760616
        if not self._has_systemd_suffix():
            return super().is_enabled
        raise RuntimeError(
            "Unable to determine state of {0}. Does this service exist?".format(
                self.name
            )
        )

    @property
    def is_valid(self):
        # systemd-analyze requires a full unit name.
        if self._has_systemd_suffix():
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

    @property
    def is_masked(self):
        cmd = self.run_test("systemctl is-enabled %s", self.name)
        return cmd.stdout.strip() == "masked"

    @functools.cached_property
    def systemd_properties(self):
        out = self.check_output("systemctl show %s", self.name)
        out_d = {}
        if out:
            # maxsplit is required because values can contain `=`
            out_d = dict(
                map(lambda pair: pair.split("=", maxsplit=1), out.splitlines())
            )
        return out_d


class UpstartService(SysvService):
    @property
    def exists(self):
        return self._host.file(f"/etc/init/{self.name}.conf").exists

    @property
    def is_enabled(self):
        if (
            self.run(
                "grep -q '^start on' /etc/init/%s.conf",
                self.name,
            ).rc
            == 0
            and self.run(
                "grep -q '^manual' /etc/init/%s.override",
                self.name,
            ).rc
            != 0
        ):
            return True
        # Fallback on SysV
        return super().is_enabled

    @property
    def is_running(self):
        cmd = self.run_test("status %s", self.name)
        if cmd.rc == 0 and len(cmd.stdout.split()) > 1:
            return "running" in cmd.stdout.split()[1]
        return super().is_running


class OpenRCService(SysvService):
    @functools.cached_property
    def _service_command(self):
        return self.find_command("rc-service")

    @property
    def is_enabled(self):
        return bool(
            self.check_output(
                "find /etc/runlevels/ -name %s",
                self.name,
            )
        )


class FreeBSDService(Service):
    @property
    def exists(self):
        return self._host.file(f"/etc/rc.d/{self.name}").exists

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
    def exists(self):
        return self._host.file(f"/etc/rc.d/{self.name}").exists

    @property
    def is_running(self):
        return self.run_test("/etc/rc.d/%s check", self.name).rc == 0

    @property
    def is_enabled(self):
        if self.name in self.check_output("rcctl ls on").splitlines():
            return True
        if self.name in self.check_output("rcctl ls off").splitlines():
            return False
        raise RuntimeError(
            f"Unable to determine state of {self.name}. Does this service exist?"
        )


class NetBSDService(Service):
    @property
    def exists(self):
        return self._host.file(f"/etc/rc.d/{self.name}").exists

    @property
    def is_running(self):
        return self.run_test("/etc/rc.d/%s onestatus", self.name).rc == 0

    @property
    def is_enabled(self):
        raise NotImplementedError


class WindowsService(Service):
    @property
    def exists(self):
        out = self.check_output(
            f"Get-Service -Name {self.name} -ErrorAction SilentlyContinue"
        )
        return self.name in out

    @property
    def is_running(self):
        return (
            self.check_output(
                "Get-Service '%s' | Select -ExpandProperty Status",
                self.name,
            )
            == "Running"
        )

    @property
    def is_enabled(self):
        return (
            self.check_output(
                "Get-Service '%s' | Select -ExpandProperty StartType",
                self.name,
            )
            == "Automatic"
        )
