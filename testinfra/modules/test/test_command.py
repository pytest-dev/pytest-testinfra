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

from testinfra.modules import Command


def test_run(mock_subprocess):
    mock_subprocess().configure_mock(**{
        "communicate.return_value": (b"out", b"err"),
        "returncode": 42,
    })
    cmd = Command("ls %s", "; rm -rf /foo")
    assert cmd.stdout == "out"
    assert cmd.stderr == "err"
    assert cmd.command == """ls '; rm -rf /foo'"""
    assert cmd.rc == 42


def test_check_output(mock_subprocess):
    mock_subprocess().configure_mock(**{
        "communicate.return_value": (b"out", b""),
        "returncode": 0,
    })
    assert Command.check_output("zzzzzzz") == "out"


def test_check_output_error(mock_subprocess):
    mock_subprocess().configure_mock(**{
        "communicate.return_value": (b"", b""),
        "returncode": 127,
    })
    with pytest.raises(AssertionError):
        Command.check_output("zzzzzzz")
