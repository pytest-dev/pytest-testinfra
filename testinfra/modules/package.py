# -*- coding: utf8 -*-
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

from testinfra import check_output
from testinfra import get_system_info
from testinfra import run


class BasePackage(object):

    def __init__(self, name):
        self.name = name
        super(BasePackage, self).__init__()

    @property
    def is_installed(self):
        raise NotImplementedError

    @property
    def version(self):
        raise NotImplementedError

    def __repr__(self):
        return "<package %s>" % (self.name,)


class DebianPackage(BasePackage):

    @property
    def is_installed(self):
        return run((
            "dpkg-query -f '${Status}' -W %s | "
            "grep -E '^(install|hold) ok installed$'"), self.name).rc == 0

    @property
    def version(self):
        return check_output((
            "dpkg-query -f '${Status} ${Version}' -W %s | "
            "sed -n 's/^install ok installed //p'"), self.name)


def Package(name):
    if get_system_info().distribution == "debian":
        return DebianPackage(name)
    else:
        raise NotImplementedError
