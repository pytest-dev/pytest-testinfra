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


class Command(Module):
    """Run commands and test stdout/stderr and exit status"""

    def __call__(self, command, *args, **kwargs):
        return self.run(command, *args, **kwargs)

    def __repr__(self):
        return "<command>"

    @classmethod
    def as_fixture(cls):
        @pytest.fixture(scope="session")
        def f(testinfra_backend):
            return Command()
        f.__doc__ = cls.__doc__
        return f
