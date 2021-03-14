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

import json
import re
import warnings

from testinfra.modules.base import Module


def _re_match(line, regexp):
    match = regexp.match(line)
    if match is None:
        raise RuntimeError("could not parse {0}".format(line))
    return match.groups()


class Pip(Module):
    """Test pip package manager and packages"""

    def __init__(self, name, pip_path="pip"):
        self.name = name
        self.pip_path = pip_path
        super().__init__()

    @property
    def is_installed(self):
        """Test if the package is installed

        >>> host.package("pip").is_installed
        True
        """
        return self.run_test("%s show %s", self.pip_path, self.name).rc == 0

    @property
    def version(self):
        """Return package version as returned by pip

        >>> host.package("pip").version
        '18.1'
        """
        return self.check_output(
            "%s show %s | grep Version: | cut -d' ' -f2",
            self.pip_path,
            self.name,
        )

    @classmethod
    def check(cls, pip_path="pip"):
        """Verify installed packages have compatible dependencies.

        >>> cmd = host.pip_package.check()
        >>> cmd.rc
        0
        >>> cmd.stdout
        No broken requirements found.

        Can only be used if `pip check`_ command is available,
        for pip versions >= 9.0.0_.

        .. _pip check: https://pip.pypa.io/en/stable/reference/pip_check/
        .. _9.0.0: https://pip.pypa.io/en/stable/news/#id526
        """
        return cls.run_expect([0, 1], "%s check", pip_path)

    @classmethod
    def get_packages(cls, pip_path="pip"):
        """Get all installed packages and versions returned by `pip list`:

        >>> host.pip_package.get_packages(pip_path='~/venv/website/bin/pip')
        {'Django': {'version': '1.10.2'},
         'mywebsite': {'version': '1.0a3', 'path': '/srv/website'},
         'psycopg2': {'version': '2.6.2'}}
        """
        out = cls.run_expect([0, 2], "%s list --no-index --format=json", pip_path)
        pkgs = {}
        if out.rc == 0:
            for pkg in json.loads(out.stdout):
                # XXX: --output=json does not return install path
                pkgs[pkg["name"]] = {"version": pkg["version"]}
        else:
            # pip < 9
            output_re = re.compile(r"^(.+) \((.+)\)$")
            for line in cls.check_output("%s list --no-index", pip_path).splitlines():
                if line.startswith("Warning: "):
                    # Warning: cannot find svn location for ...
                    continue
                name, version = _re_match(line, output_re)
                if "," in version:
                    version, path = version.split(",", 1)
                    pkgs[name] = {"version": version, "path": path.strip()}
                else:
                    pkgs[name] = {"version": version}
        return pkgs

    @classmethod
    def get_outdated_packages(cls, pip_path="pip"):
        """Get all outdated packages with current and latest version

        >>> host.pip_package.get_outdated_packages(
        ...     pip_path='~/venv/website/bin/pip')
        {'Django': {'current': '1.10.2', 'latest': '1.10.3'}}
        """
        out = cls.run_expect([0, 2], "%s list -o --format=json", pip_path)
        pkgs = {}
        if out.rc == 0:
            for pkg in json.loads(out.stdout):
                pkgs[pkg["name"]] = {
                    "current": pkg["version"],
                    "latest": pkg["latest_version"],
                }
        else:
            # pip < 9
            # pip 8: pytest (3.4.2) - Latest: 3.5.0 [wheel]
            # pip < 8: pytest (Current: 3.4.2 Latest: 3.5.0 [wheel])
            regexpes = [
                re.compile(r"^(.+?) \((.+)\) - Latest: (.+) .*$"),
                re.compile(r"^(.+?) \(Current: (.+) Latest: (.+) .*$"),
            ]
            for line in cls.check_output("%s list -o", pip_path).splitlines():
                if line.startswith("Warning: "):
                    # Warning: cannot find svn location for ...
                    continue
                output_re = regexpes[1] if "Current:" in line else regexpes[0]
                name, current, latest = _re_match(line, output_re)
                pkgs[name] = {"current": current, "latest": latest}
        return pkgs


class PipPackage(Pip):
    """.. deprecated:: 6.2

    Use :class:`~testinfra.modules.pip.Pip` instead.
    """

    @staticmethod
    def _deprecated():
        """Raise a `DeprecationWarning`"""
        warnings.warn(
            "Calling host.pip_package is deprecated, call host.pip instead",
            DeprecationWarning,
        )

    @classmethod
    def check(cls, pip_path="pip"):
        PipPackage._deprecated()
        return super().check(pip_path=pip_path)

    @classmethod
    def get_packages(cls, pip_path="pip"):
        PipPackage._deprecated()
        return super().get_packages(pip_path=pip_path)

    @classmethod
    def get_outdated_packages(cls, pip_path="pip"):
        PipPackage._deprecated()
        return super().get_outdated_packages(pip_path=pip_path)
