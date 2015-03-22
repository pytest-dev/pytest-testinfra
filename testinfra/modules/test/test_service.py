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


@pytest.mark.parametrize("rc,expected", [(0, True), (3, False)],
                         ids=["running", "not running"])
def test_is_running(Service, mock_subprocess, rc, expected):
    mock_subprocess().configure_mock(**{
        "communicate.return_value": (b"", b""),
        "returncode": rc,
    })
    assert Service("nginx").is_running is expected


@pytest.mark.parametrize("rc,expected", [(0, True), (1, False)],
                         ids=["enabled", "not enabled"])
def test_is_enabled(Service, mock_subprocess, rc, expected):
    mock_subprocess().configure_mock(**{
        "communicate.return_value": (b"", b""),
        "returncode": rc,
    })
    assert Service("nginx").is_enabled is expected
