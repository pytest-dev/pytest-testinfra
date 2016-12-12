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


class File(Module):
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
        return self.run_test("test -e %s", self.path).rc == 0

    @property
    def is_file(self):
        return self.run_test("test -f %s", self.path).rc == 0

    @property
    def is_directory(self):
        return self.run_test("test -d %s", self.path).rc == 0

    @property
    def is_pipe(self):
        return self.run_test("test -p %s", self.path).rc == 0

    @property
    def is_socket(self):
        return self.run_test("test -S %s", self.path).rc == 0

    @property
    def is_symlink(self):
        return self.run_test("test -L %s", self.path).rc == 0

    @property
    def linked_to(self):
        """Resolve symlink

        >>> File("/var/lock").linked_to
        '/run/lock'
        """
        return self.check_output("readlink -f %s", self.path)

    @property
    def user(self):
        """Return file owner as string

        >>> File("/etc/passwd").user
        'root'
        """
        raise NotImplementedError

    @property
    def uid(self):
        """Return file user id as integer

        >>> File("/etc/passwd").uid
        0
        """
        raise NotImplementedError

    @property
    def group(self):
        raise NotImplementedError

    @property
    def gid(self):
        raise NotImplementedError

    @property
    def mode(self):
        """Return file mode as octal integer

        >>> File("/etc/passwd").mode
        384  # 0o600 (octal)
        >>> File("/etc/password").mode == 0o600
        True
        >>> oct(File("/etc/password").mode) == '0600'
        True

        Note: Python 3 oct(x)_ function will produce ``'0o600'``

        You can also utilize the file mode constants from
        the stat_ library for testing file mode.

        >>> import stat
        >>> File("/etc/password").mode == stat.S_IRUSR | stat.S_IWUSR
        True

        .. _oct(x): https://docs.python.org/3.5/library/functions.html#oct
        .. _stat: https://docs.python.org/2/library/stat.html
        """
        raise NotImplementedError

    def contains(self, pattern):
        return self.run_test("grep -qs -- %s %s", pattern, self.path).rc == 0

    @property
    def md5sum(self):
        raise NotImplementedError

    @property
    def sha256sum(self):
        raise NotImplementedError

    def _get_content(self, decode):
        out = self.run_test("cat -- %s", self.path)
        if out.rc != 0:
            raise RuntimeError("Unexpected output %s" % (out,))
        if decode:
            return out.stdout
        else:
            return out.stdout_bytes

    @property
    def content(self):
        """Return file content as bytes

        >>> File("/tmp/foo").content
        b'caf\\xc3\\xa9'
        """
        return self._get_content(False)

    @property
    def content_string(self):
        """Return file content as string

        >>> File("/tmp/foo").content_string
        'café'
        """
        return self._get_content(True)

    @property
    def mtime(self):
        """Return time of last modification as datetime.datetime object

        >>> File("/etc/passwd").mtime
        datetime.datetime(2015, 3, 15, 20, 25, 40)
        """
        raise NotImplementedError

    @property
    def size(self):
        """Return size of file in bytes"""
        raise NotImplementedError

    def __repr__(self):
        return "<file %s>" % (self.path,)

    @classmethod
    def get_module_class(cls, _backend):
        SystemInfo = _backend.get_module("SystemInfo")
        if SystemInfo.type == "linux":
            return GNUFile
        elif SystemInfo.type == "netbsd":
            return NetBSDFile
        elif SystemInfo.type.endswith("bsd") or SystemInfo.type == "darwin":
            return BSDFile
        else:
            raise NotImplementedError


class GNUFile(File):
    @property
    def user(self):
        return self.check_output("stat -c %%U %s", self.path)

    @property
    def uid(self):
        return int(self.check_output("stat -c %%u %s", self.path))

    @property
    def group(self):
        return self.check_output("stat -c %%G %s", self.path)

    @property
    def gid(self):
        return int(self.check_output("stat -c %%g %s", self.path))

    @property
    def mode(self):
        # Supply a base of 8 when parsing an octal integer
        # e.g. int('644', 8) -> 420
        return int(self.check_output("stat -c %%a %s", self.path), 8)

    @property
    def mtime(self):
        ts = self.check_output("stat -c %%Y %s", self.path)
        return datetime.datetime.fromtimestamp(float(ts))

    @property
    def size(self):
        return int(self.check_output("stat -c %%s %s", self.path))

    @property
    def md5sum(self):
        return self.check_output("md5sum %s | cut -d' ' -f1", self.path)

    @property
    def sha256sum(self):
        return self.check_output(
            "sha256sum %s | cut -d ' ' -f 1", self.path)


class BSDFile(File):
    @property
    def user(self):
        return self.check_output("stat -f %%Su %s", self.path)

    @property
    def uid(self):
        return int(self.check_output("stat -f %%u %s", self.path))

    @property
    def group(self):
        return self.check_output("stat -f %%Sg %s", self.path)

    @property
    def gid(self):
        return int(self.check_output("stat -f %%g %s", self.path))

    @property
    def mode(self):
        # Supply a base of 8 when parsing an octal integer
        # e.g. int('644', 8) -> 420
        return int(self.check_output("stat -f %%Lp %s", self.path), 8)

    @property
    def mtime(self):
        ts = self.check_output("stat -f %%m %s", self.path)
        return datetime.datetime.fromtimestamp(float(ts))

    @property
    def size(self):
        return int(self.check_output("stat -f %%z %s", self.path))

    @property
    def md5sum(self):
        return self.check_output("md5 < %s", self.path)

    @property
    def sha256sum(self):
        return self.check_output(
            "sha256 < %s", self.path)


class NetBSDFile(BSDFile):

    @property
    def sha256sum(self):
        return self.check_output(
            "cksum -a sha256 < %s", self.path)
