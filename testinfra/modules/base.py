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

from testinfra import run


class Module(object):

    @staticmethod
    def run(command, *args, **kwargs):
        return run(command, *args, **kwargs)

    def run_expect(self, exit_status, command, *args, **kwargs):
        out = self.run(command, *args, **kwargs)
        assert out.rc in exit_status
        return out

    def run_test(self, command, *args, **kwargs):
        return self.run_expect([0, 1], command, *args, **kwargs)

    def check_output(self, command, *args, **kwargs):
        out = self.run(command, *args, **kwargs)
        assert out.rc == 0

        if out.stdout[-1] == "\n":
            return out.stdout[:-1]
        else:
            return out.stdout
