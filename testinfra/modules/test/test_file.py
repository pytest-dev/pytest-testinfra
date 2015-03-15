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

import six

from testinfra.modules import File


def test_file_content(mock_subprocess):
    content = b"".join([six.int2byte(x) for x in range(255)])
    mock_subprocess().configure_mock(**{
        "communicate.return_value": (content, b""),
        "returncode": 0,
    })
    assert File("/foo").content == content
