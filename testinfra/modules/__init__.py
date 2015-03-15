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

from testinfra.modules.command import Command
from testinfra.modules.file import File
from testinfra.modules.group import Group
from testinfra.modules.interface import Interface
from testinfra.modules.package import Package
from testinfra.modules.service import Service


class _SystemInfo(object):

    def __getattr__(self, attr):
        from testinfra import get_system_info
        return getattr(get_system_info(), attr)

system = _SystemInfo()


__all__ = [
    "Command", "File", "Package", "Group", "Interface",
    "Service", "system",
]
