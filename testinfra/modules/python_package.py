# -*- coding: utf-8 -*-
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

import re

from testinfra.modules.base import Module


class PythonPackage(Module):
    """Test status and version of Python package."""

    def __init__(self, pkg_name, pip_path='pip'):
        """If you are using a virtualenv, pass the full path to the pip binary

        :param pkg_name: Name of the package to verify
        :param pip_path: Path to the desired pip binary
        """
        super(PythonPackage, self).__init__()
        self.pip_dict = {}
        self.pkg_name = pkg_name
        cmd = '{0} list'.format(pip_path)
        py_re = re.compile(r'^([A-Za-z-_1-9]+) \((.*?)(, .*)?\)')
        for line in self.check_output(cmd).split('\n'):
            if re.match(py_re, line):
                name, version = re.search(py_re, line).groups()[:2]
                self.pip_dict[name] = version

    @property
    def is_installed(self):
        return bool(self.pip_dict.get(self.pkg_name))

    @property
    def version(self):
        return self.pip_dict.get(self.pkg_name)

    def __repr__(self):
        return "<python_package %s>" % (self.pkg_name,)
