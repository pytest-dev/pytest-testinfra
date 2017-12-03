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

pytest_plugins = ['pytester']


def test_nagios_notest(testdir):
    result = testdir.runpytest('--nagios', '-q', '--tb=no')
    assert result.ret == 0
    lines = result.stdout.str().splitlines()
    assert lines[0].startswith('TESTINFRA OK - 0 passed, 0 failed, 0 skipped')


def test_nagios_ok(testdir):
    testdir.makepyfile('def test_ok(): pass')
    result = testdir.runpytest('--nagios', '-q', '--tb=no')
    assert result.ret == 0
    lines = result.stdout.str().splitlines()
    assert lines[0].startswith('TESTINFRA OK - 1 passed, 0 failed, 0 skipped')
    assert lines[1][0] == '.'


def test_nagios_fail(testdir):
    testdir.makepyfile('def test_ok(): pass\ndef test_fail(): assert False')
    result = testdir.runpytest('--nagios', '-q', '--tb=no')
    assert result.ret == 2
    lines = result.stdout.str().splitlines()
    assert lines[0].startswith(
        'TESTINFRA CRITICAL - 1 passed, 1 failed, 0 skipped')
    assert lines[1][:2] == '.F'
