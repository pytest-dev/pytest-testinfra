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

import json
import re

from testinfra.modules.base import InstanceModule


def _re_match(line, regexp):
    match = regexp.match(line)
    if match is None:
        raise RuntimeError('could not parse {0}'.format(line))
    return match.groups()


class PipPackage(InstanceModule):
    """Test pip packages status and version"""

    def get_packages(self, pip_path="pip"):
        """Get all installed packages and versions returned by `pip list`:

        >>> host.pip_package.get_packages(pip_path='~/venv/website/bin/pip')
        {'Django': {'version': '1.10.2'},
         'mywebsite': {'version': '1.0a3', 'path': '/srv/website'},
         'psycopg2': {'version': '2.6.2'}}
        """
        out = self.run_expect(
            [0, 2], '{0} list --no-index --format=json'.format(pip_path))
        pkgs = {}
        if out.rc == 0:
            for pkg in json.loads(out.stdout):
                # XXX: --output=json does not return install path
                pkgs[pkg['name']] = {'version': pkg['version']}
        else:
            # pip < 9
            output_re = re.compile(r'^(.+) \((.+)\)$')
            for line in self.check_output(
                '{0} list --no-index'.format(pip_path)
            ).splitlines():
                if line.startswith('Warning: '):
                    # Warning: cannot find svn location for ...
                    continue
                name, version = _re_match(line, output_re)
                if ',' in version:
                    version, path = version.split(',', 1)
                    pkgs[name] = {'version': version, 'path': path.strip()}
                else:
                    pkgs[name] = {'version': version}
        return pkgs

    def get_outdated_packages(self, pip_path="pip"):
        """Get all outdated packages with current and latest version

        >>> host.pip_package.get_outdated_packages(
        ...     pip_path='~/venv/website/bin/pip')
        {'Django': {'current': '1.10.2', 'latest': '1.10.3'}}
        """
        out = self.run_expect(
            [0, 2], '{0} list -o --format=json'.format(pip_path))
        pkgs = {}
        if out.rc == 0:
            for pkg in json.loads(out.stdout):
                pkgs[pkg['name']] = {'current': pkg['version'],
                                     'latest': pkg['latest_version']}
        else:
            # pip < 9
            # pip 8: pytest (3.4.2) - Latest: 3.5.0 [wheel]
            # pip < 8: pytest (Current: 3.4.2 Latest: 3.5.0 [wheel])
            regexpes = [
                re.compile(r'^(.+?) \((.+)\) - Latest: (.+) .*$'),
                re.compile(r'^(.+?) \(Current: (.+) Latest: (.+) .*$'),
            ]
            for line in self.check_output(
                    '{0} list -o'.format(pip_path)).splitlines():
                if line.startswith('Warning: '):
                    # Warning: cannot find svn location for ...
                    continue
                output_re = regexpes[1] if 'Current:' in line else regexpes[0]
                name, current, latest = _re_match(line, output_re)
                pkgs[name] = {'current': current, 'latest': latest}
        return pkgs
