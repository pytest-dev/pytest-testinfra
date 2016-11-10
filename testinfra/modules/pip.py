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

    def get_packages(self, pip_path="pip"):
        """Get all installed packages and versions returned by `pip list`:

        >>> PipPackage.get_packages(pip_path='~/venv/website/bin/pip')
        {'Django': {'version': '1.10.2'},
         'mywebsite': {'version': '1.0a3', 'path': '/srv/website'},
         'psycopg2': {'version': '2.6.2'}}
        """
        output_re = re.compile(r'^(.+) \((.+)\)$')
        pkgs = {}
        out = self.check_output("%s list --no-index", pip_path)
        for line in out.splitlines():
            if line.startswith('Warning: '):
                # Warning: cannot find svn location for rst2pdf==0.93.dev-r0
                continue
            match = output_re.match(line)
            if match is None:
                raise RuntimeError("could not parse {0}".format(repr(line)))
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

        >>> PipPackage.get_outdated_packages(pip_path='~/venv/website/bin/pip')
        {'Django': {'current': '1.10.2', 'latest': '1.10.3'}}
        """
        output_re = [re.compile(r) for r in [
            # newer pip
            r'^(.+) \(Current: (.+) Latest: (.+)\)$',
            # old pip
            r'^(.+) \((.+)\) - Latest: (.+) .*$',
        ]]
        pkgs = {}
        out = self.check_output("%s list -o", pip_path)
        for line in out.splitlines():
            # Warning: cannot find svn location for rst2pdf==0.93.dev-r0
            # Could not find any downloads that satisfy the requirement iotop
            if line.startswith('Warning: ') or line.startswith('Could not '):
                continue
            for out_re in output_re:
                match = out_re.match(line)
                if match:
                    name, current, latest = match.groups()
                    pkgs[name] = {'current': current, 'latest': latest}
                    break
            else:
                raise RuntimeError("could not parse {0}".format(repr(line)))
        return pkgs
