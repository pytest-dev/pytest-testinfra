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

import pytest


@pytest.mark.integration
def test_package(Package, SystemInfo):
    assert Package("zsh").is_installed
    if (
        SystemInfo.type, SystemInfo.distribution, SystemInfo.codename,
    ) == ("linux", "debian", "wheezy"):
        version = "4.3.17-1"
    elif (
        SystemInfo.type, SystemInfo.release,
    ) == ("freebsd", "10.1-RELEASE"):
        version = "5.0.7_2"
    elif (
        SystemInfo.type, SystemInfo.release,
    ) == ("netbsd", "6.1.5"):
        version = "5.0.7nb1"
    elif (
        SystemInfo.type, SystemInfo.release,
    ) == ("openbsd", "5.6"):
        version = "5.0.5p0"
    else:
        pytest.skip()

    assert Package("zsh").version == version
