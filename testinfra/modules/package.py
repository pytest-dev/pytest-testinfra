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

import pytest

from testinfra.modules.base import Module


class Package(Module):
    """Test packages status and version"""

    def __init__(self, name):
        self.name = name
        super(Package, self).__init__()

    @property
    def is_installed(self):
        raise NotImplementedError

    @property
    def version(self):
        raise NotImplementedError

    def __repr__(self):
        return "<package %s>" % (self.name,)

    @classmethod
    def as_fixture(cls):
        @pytest.fixture(scope="session")
        def f(Command):
            if Command.run_test("which apt-get").rc == 0:
                return DebianPackage
            else:
                raise NotImplementedError
        f.__doc__ = cls.__doc__
        return f


class DebianPackage(Package):

    @property
    def is_installed(self):
        return self.run_test((
            "dpkg-query -f '${Status}' -W %s | "
            "grep -qE '^(install|hold) ok installed$'"), self.name).rc == 0

    @property
    def version(self):
        return self.check_output((
            "dpkg-query -f '${Status} ${Version}' -W %s | "
            "sed -n 's/^install ok installed //p'"), self.name)
