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

from testinfra.modules.base import Module


class User(Module):
    """Test unix users

    If name is not supplied, test the current user
    """

    def __init__(self, name=None):
        self._name = name
        super(User, self).__init__()

    @property
    def name(self):
        """Return user name"""
        if self._name is None:
            self._name = self.check_output("id -nu")
        return self._name

    @property
    def exists(self):
        return self.run_test("id %s", self.name).rc == 0

    @property
    def uid(self):
        """Return user ID"""
        return int(self.check_output("id -u %s", self.name))

    @property
    def gid(self):
        """Return effective group ID"""
        return int(self.check_output("id -g %s", self.name))

    @property
    def group(self):
        """Return effective group name"""
        return self.check_output("id -ng %s", self.name)

    @property
    def gids(self):
        """Return the list of user group IDs"""
        return [int(gid) for gid in self.check_output(
            "id -G %s", self.name,
        ).split(" ")]

    @property
    def groups(self):
        """Return the list of user group names"""
        return self.check_output("id -nG %s", self.name).split(" ")

    @property
    def home(self):
        """Return the user home directory"""
        return self.check_output("getent passwd %s", self.name).split(":")[5]

    @property
    def shell(self):
        """Return the user login shell"""
        return self.check_output("getent passwd %s", self.name).split(":")[6]

    def __repr__(self):
        return "<user %s>" % (self.name,)
