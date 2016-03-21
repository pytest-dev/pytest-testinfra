# -*- coding: utf8 -*-
# Copyright © 2016 Jimmy Tang <jimmy_tang@rapid7.com>
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


class Supervisor(Module):
    """Test supervisor managed processes
    """

    def __init__(self, name):
        self.name = name
        super(Supervisor, self).__init__()

    @property
    def is_running(self):
        """Test if service is running"""
        raise NotImplementedError

    @property
    def is_enabled(self):
        """Test if service is enabled"""
        raise NotImplementedError

    @classmethod
    def get_module_class(cls, _backend):
        Command = _backend.get_module("Command")
        if (
            Command.run_test("which supervisorctl").rc == 0
            ):
            return SupervisorService
        else:
            raise NotImplementedError

    def __repr__(self):
        return "<service %s>" % (self.name,)


class SupervisorService(Supervisor):
    @property
    def is_running(self):
        # 0: program running
        # anything else is not considered, the supervisorctl program
        # always returns zero no matter what
        return self.run_expect(
                [0], "supervisorctl status %s | grep RUNNING" % self.name).rc == 0
