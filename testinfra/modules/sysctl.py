# -*- coding: utf-8 -*-
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

from testinfra.modules.base import InstanceModule


class Sysctl(InstanceModule):
    """Test kernel parameters

    >>> Sysctl("kernel.osrelease")
    "3.16.0-4-amd64"
    >>> Sysctl("vm.dirty_ratio")
    20
    """

    def __call__(self, name):
        value = self.check_output("sysctl -n %s", name)
        try:
            return int(value)
        except ValueError:
            return value

    def __repr__(self):
        return "<sysctl>"
