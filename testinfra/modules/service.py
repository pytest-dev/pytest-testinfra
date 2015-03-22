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

from testinfra.modules.base import Module


class Service(Module):
    """Test services"""

    def __init__(self, name):
        self.name = name
        super(Service, self).__init__()

    @property
    def is_running(self):
        out = self.run("service %s status", self.name)
        assert out.rc != 127, "Unexpected exit status 127"
        return out.rc == 0

    @property
    def is_enabled(self):
        return self.is_enabled_with_level(3)

    def is_enabled_with_level(self, level):
        # sysv
        if self.run_test(
            "ls /etc/rc%s.d | grep -q 'S..%s'",
            str(level), self.name
        ).rc == 0:
            return True
        # systemd
        elif self.run(
            "grep -q 'start on' /etc/init/%s.conf", self.name
        ).rc == 0:
            return True
        else:
            return False

    def __repr__(self):
        return "<service %s>" % (self.name,)
