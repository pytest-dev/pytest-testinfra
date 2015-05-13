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
def test_package_bash(_testinfra_host, Package):
    bash = Package("bash")
    version = {
        "debian_wheezy": "4.2+dfsg-0.1+deb7u3",
        "debian_jessie": "4.3-11+b1",
        "ubuntu_trusty": "4.3-7ubuntu1.5",
        "centos_7": "4.2.46",
        "fedora_21": "4.3.33",
    }[_testinfra_host]
    assert bash.is_installed
    assert bash.version == version
