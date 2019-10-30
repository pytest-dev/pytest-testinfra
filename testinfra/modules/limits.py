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

from testinfra.modules.base import InstanceModule

LIMITS_FLAGS = {
    "as": "-v",
    "core": "-c",
    "cpu": "-t",
    "data": "-d",
    "fsize": "-f",
    "locks": "-x",
    "maxlogins": "",
    "maxsyslogins": "",
    "memlock": "-l",
    "msgqueue": "-q",
    "nice": "-e",
    "nofile": "-n",
    "nproc": "-u",
    "priority": "-r",
    "rss": "-m",
    "rtprio": "-r",
    "sigpending": "-i",
    "stack": "-s"
}


class Limits(InstanceModule):
    """Test user session limits

    >>> host.limits("nofile")
    1024
    >>> host.limits("cpu")
    "unlimited"
    """

    def __call__(self, name, limit_type="soft"):
        type_flag = ""
        if limit_type == "soft":
            type_flag = "-S"
        elif limit_type == "hard":
            type_flag = "-H"
        value = self.check_output("bash -c 'ulimit %s %s'",
                                  type_flag,
                                  LIMITS_FLAGS.get(name, ""))
        try:
            return int(value)
        except ValueError:
            return value

    def __repr__(self):
        return "<limits>"
