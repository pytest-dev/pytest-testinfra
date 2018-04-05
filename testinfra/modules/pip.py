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


class PipPackage(InstanceModule):
    """Test pip packages status and version"""

    @staticmethod
    def _first_match(line, regexes):
        for r in regexes:
            match = r.match(line)
            if match is not None:
                return match
        raise RuntimeError("could not parse {0}".format(repr(line)))

    def _pip_list(self, pip_path, outdated=False):
        extras = " -o " if outdated else " --no-index "
        out = self.run_expect(
            [0, 2],
            "{} list {} --format=columns".format(pip_path, extras)
        )
        if out.rc == 0:
            lines = out.stdout.splitlines()[2:]  # drops column headers
        else:  # older version of pip, we assume
            out = self.check_output("{} list {}".format(pip_path, extras))
            lines = out.splitlines()
        return lines

    def get_packages(self, pip_path="pip"):
        """Get all installed packages and versions returned by `pip list`:

        >>> host.pip_package.get_packages(pip_path='~/venv/website/bin/pip')
        {'Django': {'version': '1.10.2'},
         'mywebsite': {'version': '1.0a3', 'path': '/srv/website'},
         'psycopg2': {'version': '2.6.2'}}
        """
        output_re = [
            re.compile(r) for r in
            [
                r'^(.+?)\s+(.+)$',  # newer pip
                r'^(.+) \((.+)\)$',  # older pip
            ]
        ]
        pkgs = {}
        lines = self._pip_list(pip_path)
        for line in lines:
            if line.startswith('Warning: '):
                # Warning: cannot find svn location for rst2pdf==0.93.dev-r0
                continue
            match = PipPackage._first_match(line.strip(), output_re)
            name, version = match.groups()
            if ',' in version:
                version, path = version.split(',', 1)
                path = path.strip()
                pkgs[name] = {'version': version, 'path': path}
            else:
                pkgs[name] = {'version': version}
        return pkgs

    def get_outdated_packages(self, pip_path="pip"):
        """Get all outdated packages with current and latest version

        >>> host.pip_package.get_outdated_packages(
        ...     pip_path='~/venv/website/bin/pip')
        {'Django': {'current': '1.10.2', 'latest': '1.10.3'}}
        """
        output_re = [
            re.compile(r) for r in
            [
                r'^(.+?)\s+(.+?)\s+(.+?)\s.*$',  # newer pip
                r'^(.+) \((.+)\) - Latest: (.+) .*$',  # older pip
            ]
        ]
        pkgs = {}
        lines = self._pip_list(pip_path, outdated=True)
        for line in lines:
            # Warning: cannot find svn location for rst2pdf==0.93.dev-r0
            # Could not find any downloads that satisfy the requirement iotop
            if line.startswith('Warning: ') or line.startswith('Could not '):
                continue
            match = PipPackage._first_match(line.strip(), output_re)
            name, current, latest = match.groups()
            pkgs[name] = {'current': current, 'latest': latest}
        return pkgs
