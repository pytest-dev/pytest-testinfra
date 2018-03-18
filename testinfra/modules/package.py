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


class Package(Module):
    """Test packages status and version"""

    def __init__(self, name):
        self.name = name
        super(Package, self).__init__()

    @property
    def is_installed(self):
        """Test if the package is installed

        >>> host.package("nginx").is_installed
        True

        Supported package systems:

        - apk (Alpine)
        - apt (Debian, Ubuntu, ...)
        - pacman (Arch)
        - pkg (FreeBSD)
        - pkg_info (NetBSD)
        - pkg_info (OpenBSD)
        - rpm (RHEL, Centos, Fedora, ...)
        """
        raise NotImplementedError

    @property
    def release(self):
        """Return the release specific info from the package version

        >>> host.package("nginx").release
        '1.el6'
        """
        raise NotImplementedError

    @property
    def version(self):
        """Return package version as returned by the package system

        >>> host.package("nginx").version
        '1.2.1-2.2+wheezy3'
        """
        raise NotImplementedError

    def __repr__(self):
        return "<package %s>" % (self.name,)

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "freebsd":
            return FreeBSDPackage
        elif host.system_info.type in ("openbsd", "netbsd"):
            return OpenBSDPackage
        elif host.exists("dpkg-query"):
            return DebianPackage
        elif host.exists("rpm"):
            return RpmPackage
        elif host.exists("apk"):
            return AlpinePackage
        elif host.system_info.distribution == "arch":
            return ArchPackage
        else:
            raise NotImplementedError


class DebianPackage(Package):

    @property
    def is_installed(self):
        out = self.check_output("dpkg-query -f '${Status}' -W %s" % (
            self.name,)).split()
        installed_status = ["ok", "installed"]
        return out[0] in ["install", "hold"] and out[1:3] == installed_status

    @property
    def release(self):
        raise NotImplementedError

    @property
    def version(self):
        out = self.check_output("dpkg-query -f '${Status} ${Version}' -W %s"
                                % (self.name,)).split()
        if out[0].lower() in ["install", "hold"]:
            return out[3]


class FreeBSDPackage(Package):

    @property
    def is_installed(self):
        EX_UNAVAILABLE = 69
        return self.run_expect(
            [0, EX_UNAVAILABLE], "pkg query %%n %s", self.name).rc == 0

    @property
    def release(self):
        raise NotImplementedError

    @property
    def version(self):
        return self.check_output("pkg query %%v %s", self.name)


class OpenBSDPackage(Package):

    @property
    def is_installed(self):
        return self.run_test("pkg_info -e %s", "%s-*" % (self.name,)).rc == 0

    @property
    def release(self):
        raise NotImplementedError

    @property
    def version(self):
        out = self.check_output("pkg_info -e %s", "%s-*" % (self.name,))
        # OpenBSD: inst:zsh-5.0.5p0
        # NetBSD: zsh-5.0.7nb1
        return out.split(self.name + "-", 1)[1]


class RpmPackage(Package):

    @property
    def is_installed(self):
        return self.run_test("rpm -q %s", self.name).rc == 0

    @property
    def version(self):
        return self.check_output('rpm -q --queryformat="%%{VERSION}" %s',
                                 self.name)

    @property
    def release(self):
        return self.check_output('rpm -q --queryformat="%%{RELEASE}" %s',
                                 self.name)


class AlpinePackage(Package):

    @property
    def is_installed(self):
        return self.run_test("apk -e info %s", self.name).rc == 0

    @property
    def version(self):
        out = self.check_output("apk -e -v info %s", self.name).split("-")
        return out[-2]

    @property
    def release(self):
        out = self.check_output("apk -e -v info %s", self.name).split("-")
        return out[-1]


class ArchPackage(Package):

    @property
    def is_installed(self):
        return self.run_test("pacman -Q %s", self.name).rc == 0

    @property
    def version(self):
        out = self.check_output("pacman -Q %s", self.name).split(" ")
        return out[1]

    @property
    def release(self):
        raise NotImplementedError
