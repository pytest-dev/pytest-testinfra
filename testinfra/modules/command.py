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


class Command(InstanceModule):
    """Run given command and return rc (exit status), stdout and stderr

    >>> cmd = Command("ls -l /etc/passwd")
    >>> cmd.rc
    0
    >>> cmd.stdout
    '-rw-r--r-- 1 root root 1790 Feb 11 00:28 /etc/passwd\\n'
    >>> cmd.stderr
    ''


    Good practice: always use shell arguments quoting to avoid shell injection


    >>> cmd = Command("ls -l -- %s", "/;echo inject")
    CommandResult(
        rc=2, stdout='',
        stderr='ls: cannot access /;echo inject: No such file or directory\\n',
        command="ls -l '/;echo inject'")
    """

    def __call__(self, command, *args, **kwargs):
        return self.run(command, *args, **kwargs)

    def exists(self, command):
        """Return True if given command exist in $PATH"""
        return self.run_expect([0, 1, 127], "command -v %s", command).rc == 0

    def __repr__(self):
        return "<command>"
