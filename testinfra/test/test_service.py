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
def test_ssh_service(_testinfra_host, Service, SystemInfo):
    if _testinfra_host in (
        "ubuntu_trusty", "debian_wheezy", "debian_jessie",
    ):
        ssh = Service("ssh")
        assert ssh.is_running
        assert ssh.is_enabled
    else:
        pytest.skip()
