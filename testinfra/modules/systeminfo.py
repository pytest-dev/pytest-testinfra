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

import re

from testinfra.modules.base import InstanceModule
from testinfra.utils import cached_property


class SystemInfo(InstanceModule):
    """Return system informations"""

    @cached_property
    def sysinfo(self):
        sysinfo = {
            "type": None,
            "distribution": None,
            "codename": None,
            "release": None,
        }
        sysinfo["type"] = self.check_output("uname -s").lower()
        if sysinfo["type"] == "linux":
            sysinfo.update(**self._get_linux_sysinfo())
        elif sysinfo["type"] == "darwin":
            sysinfo.update(**self._get_darwin_sysinfo())
        else:
            # BSD
            sysinfo["release"] = self.check_output("uname -r")
            sysinfo["distribution"] = sysinfo["type"]
            sysinfo["codename"] = None
        return sysinfo

    def _get_linux_sysinfo(self):
        sysinfo = {}

        # LSB
        lsb = self.run("lsb_release -a")
        if lsb.rc == 0:
            for line in lsb.stdout.splitlines():
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip().lower()
                if key == "distributor id":
                    sysinfo["distribution"] = value
                elif key == "release":
                    sysinfo["release"] = value
                elif key == "codename":
                    sysinfo["codename"] = value
            return sysinfo

        # https://www.freedesktop.org/software/systemd/man/os-release.html
        os_release = self.run("cat /etc/os-release")
        if os_release.rc == 0:
            for line in os_release.stdout.splitlines():
                for key, attname in (
                    ("ID=", "distribution"),
                    ("VERSION_ID=", "release"),
                    ("VERSION_CODENAME=", "codename"),
                ):
                    if line.startswith(key):
                        sysinfo[attname] = (
                            line[len(key):].replace('"', "").
                            replace("'", "").strip())
            # Arch doesn't have releases
            if sysinfo["distribution"] == "arch":
                sysinfo["release"] = "rolling"
            return sysinfo

        # RedHat / CentOS 6 haven't /etc/os-release
        redhat_release = self.run("cat /etc/redhat-release")
        if redhat_release.rc == 0:
            match = re.match(
                r"^(.+) release ([^ ]+) .*$",
                redhat_release.stdout.strip())
            if match:
                sysinfo["distribution"], sysinfo["release"] = (
                    match.groups())
                return sysinfo

        # Alpine doesn't have /etc/os-release
        alpine_release = self.run("cat /etc/alpine-release")
        if alpine_release.rc == 0:
            sysinfo["distribution"] = "alpine"
            sysinfo["release"] = alpine_release.stdout.strip()
            return sysinfo

        return sysinfo

    def _get_darwin_sysinfo(self):
        sysinfo = {}

        sw_vers = self.run("sw_vers")
        if sw_vers.rc == 0:
            for line in sw_vers.stdout.splitlines():
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                if key == "productname":
                    sysinfo["distribution"] = value
                elif key == "productversion":
                    sysinfo["release"] = value

        return sysinfo

    @property
    def type(self):
        """OS type

        >>> host.system_info.type
        'linux'
        """
        return self.sysinfo["type"]

    @property
    def distribution(self):
        """Distribution name

        >>> host.system_info.distribution
        'debian'
        """
        return self.sysinfo["distribution"]

    @property
    def release(self):
        """Distribution release number

        >>> host.system_info.release
        '7.8'
        """
        return self.sysinfo["release"]

    @property
    def codename(self):
        """Release code name

        >>> host.system_info.codename
        'wheezy'
        """
        return self.sysinfo["codename"]
