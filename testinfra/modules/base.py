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
from testinfra import get_backend


class Module(object):

    @staticmethod
    def run(command, *args, **kwargs):
        return get_backend().run(command, *args, **kwargs)

    @classmethod
    def run_expect(cls, expected, command, *args, **kwargs):
        """Run command and check it return an expected exit status

        :param expected: A list of expected exit status
        :raises: AssertionError
        """
        __tracebackhide__ = True
        out = cls.run(command, *args, **kwargs)
        if out.rc not in expected:
            pytest.fail("Unexpected exit code %s for %s" % (out.rc, out))
        return out

    @classmethod
    def run_test(cls, command, *args, **kwargs):
        """Run command and check it return an exit status of 0 or 1

        :raises: AssertionError
        """
        return cls.run_expect([0, 1], command, *args, **kwargs)

    @classmethod
    def check_output(cls, command, *args, **kwargs):
        """Get stdout of a command which has run successfully

        :returns: stdout without trailing newline
        :raises: AssertionError
        """
        __tracebackhide__ = True
        out = cls.run(command, *args, **kwargs)
        if out.rc != 0:
            pytest.fail("Unexpected exit code %s for %s" % (out.rc, out))

        if out.stdout[-1] == "\n":
            return out.stdout[:-1]
        else:
            return out.stdout

    @classmethod
    def as_fixture(cls):
        @pytest.fixture(scope="session")
        def f(testinfra_backend):
            return cls
        f.__doc__ = cls.__doc__
        return f
