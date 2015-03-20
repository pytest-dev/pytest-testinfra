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


from testinfra import get_system_info


def test_osinfo(mock_subprocess):
    values = [
        # uname -s
        (b"Linux\n", b""),
        # lsb_release -a
        ((
            b"Distributor ID: Debian\n"
            b"Description:    Debian GNU/Linux 7.8 (wheezy)\n"
            b"Release:        7.8\n"
            b"Codename:       wheezy\n"
        ), b"No LSB modules are available.\n"),
    ]
    mock_subprocess().configure_mock(**{
        "communicate.side_effect": values,
        "returncode": 0,
    })
    info = get_system_info()
    assert info.type == "linux"
    assert info.distribution == "debian"
    assert info.release == "7.8"
    assert info.codename == "wheezy"
