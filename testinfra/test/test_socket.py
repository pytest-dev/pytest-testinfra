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

from testinfra.modules.socket import parse_socketspec


def test_parse_socketspec():
    assert parse_socketspec("tcp://22") == ("tcp", None, 22)
    assert parse_socketspec("tcp://:::22") == ("tcp", "::", 22)
    assert parse_socketspec("udp://0.0.0.0:22") == ("udp", "0.0.0.0", 22)
    assert parse_socketspec("unix://can:be.any/thing:22") == (
        "unix", "can:be.any/thing:22", None)
