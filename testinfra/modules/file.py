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

import datetime

from testinfra import check_output
from testinfra import run


class File(object):
    """Test various files attributes"""

    def __init__(self, path):
        self.path = path
        super(File, self).__init__()

    @property
    def exists(self):
        """Test if file exists

        >>> File("/etc/passwd").exists
        True
        >>> File("/nonexistent").exists
        False

        """
        return run("test -e %s", self.path).rc == 0

    @property
    def is_file(self):
        return run("test -f %s", self.path).rc == 0

    @property
    def is_directory(self):
        return run("test -d %s", self.path).rc == 0

    @property
    def is_pipe(self):
        return run("test -p %s", self.path).rc == 0

    @property
    def is_socket(self):
        return run("test -S %s", self.path).rc == 0

    @property
    def is_symlink(self):
        return run("test -L %s", self.path).rc == 0

    @property
    def linked_to(self):
        """Resolve symlink

        >>> File("/var/lock").linked_to
        '/run/lock'
        """
        return check_output("readlink -f %s", self.path)

    @property
    def user(self):
        """Return file owner as string

        >>> File("/etc/passwd").group
        'root'
        """
        return check_output("stat -c %%U %s", self.path)

    @property
    def uid(self):
        """Return file user id as integer

        >>> File("/etc/passwd").uid
        0
        """
        return int(check_output("stat -c %%u %s", self.path))

    @property
    def group(self):
        return check_output("stat -c %%G %s", self.path)

    @property
    def gid(self):
        return int(check_output("stat -c %%g %s", self.path))

    @property
    def mode(self):
        """Return file mode as integer

        >>> File("/etc/passwd").mode
        644
        """
        return int(check_output("stat -c %%a %s", self.path))

    def contains(self, pattern):
        return run("grep -qs -- %s %s", pattern, self.path).rc == 0

    @property
    def md5sum(self):
        return check_output("md5sum %s | cut -d' ' -f1", self.path)

    @property
    def sha256sum(self):
        return check_output(
            "sha256sum %s | cut -d ' ' -f 1", self.path)

    def _get_content(self, decode):
        out = run("cat -- %s", self.path, decode=decode)
        if out.rc != 0:
            raise RuntimeError("Unexpected output %s" % (out,))
        return out.stdout

    @property
    def content(self):
        """Return file content as bytes

        >>> File("/tmp/foo").content
        b'bar'
        """
        return self._get_content(False)

    @property
    def content_string(self):
        """Return file content as string

        >>> File("/tmp/foo").content
        'bar'
        """
        return self._get_content(True)

    @property
    def mtime(self):
        """Return time of last modification as datetime.datetime object

        >>> File("/etc/passwd").mtime
        datetime.datetime(2015, 3, 15, 20, 25, 40)
        """
        ts = check_output("stat -c %%Y %s", self.path)
        return datetime.datetime.fromtimestamp(float(ts))

    @property
    def size(self):
        """Return size of file in bytes"""
        return int(check_output("stat -c %%s %s", self.path))

    def __repr__(self):
        return "<file %s>" % (self.path,)
