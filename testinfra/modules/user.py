# coding: utf-8
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

import datetime

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

    @property
    def password(self):
        """Return the crypted user password"""
        return self.check_output("getent shadow %s", self.name).split(":")[1]

    @property
    def gecos(self):
        """Return the user comment/gecos field"""
        return self.check_output("getent passwd %s", self.name).split(":")[4]

    @property
    def expiration_date(self):
        """Return the account expiration date

        >>> host.user("phil").expiration_date
        datetime.datetime(2020, 1, 1, 0, 0)
        >>> host.user("root").expiration_date
        None
        """
        days = self.check_output("getent shadow %s", self.name).split(":")[7]
        try:
            days = int(days)
        except ValueError:
            return None

        if days > 0:
            epoch = datetime.datetime.utcfromtimestamp(0)
            return epoch + datetime.timedelta(days=int(days))

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type.endswith("bsd"):
            return BSDUser
        return super(User, cls).get_module_class(host)

    def __repr__(self):
        return "<user %s>" % (self.name,)


class BSDUser(User):

    @property
    def password(self):
        return self.check_output("getent passwd %s", self.name).split(":")[1]

    @property
    def expiration_date(self):
        seconds = self.check_output(
            "getent passwd %s", self.name).split(":")[6]
        try:
            seconds = int(seconds)
        except ValueError:
            return None

        if seconds > 0:
            epoch = datetime.datetime.utcfromtimestamp(0)
            return epoch + datetime.timedelta(seconds=int(seconds))
