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


class RubyPackage(Module):
    """Test status and version of Ruby gem"""

    def __init__(self, pkg_name, gem_binary='gem'):
        super(RubyPackage, self).__init__()
        self.gem_dict = {}
        self.pkg_name = pkg_name
        args = ['%s list', gem_binary]
        for line in self.check_output(*args).split('\n'):
            gem_re = re.compile(r'^([A-Za-z-_1-9]+) \((.*?)\)$')
            if re.match(gem_re, line):
                name, version = re.search(gem_re, line).groups()
                self.gem_dict[name] = version

    @property
    def is_installed(self):
        return bool(self.gem_dict.get(self.pkg_name))

    @property
    def version(self):
        return self.gem_dict.get(self.pkg_name)

    def __repr__(self):
        return "<ruby_package %s>" % (self.pkg_name,)
