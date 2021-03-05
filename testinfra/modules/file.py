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

import datetime

from testinfra.modules.base import Module


class File(Module):
    """Test various files attributes"""

    def __init__(self, path):
        self.path = path
        super().__init__()

    @property
    def exists(self):
        """Test if file exists

        >>> host.file("/etc/passwd").exists
        True
        >>> host.file("/nonexistent").exists
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

        >>> host.file("/var/lock").linked_to
        '/run/lock'
        """
        return self.check_output("readlink -f %s", self.path)

    @property
    def user(self):
        """Return file owner as string

        >>> host.file("/etc/passwd").user
        'root'
        """
        raise NotImplementedError

    @property
    def uid(self):
        """Return file user id as integer

        >>> host.file("/etc/passwd").uid
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

        >>> host.file("/etc/shadow").mode
        416  # Oo640 octal
        >>> host.file("/etc/shadow").mode == 0o640
        True
        >>> oct(host.file("/etc/shadow").mode) == '0o640'
        True

        You can also utilize the file mode constants from
        the stat_ library for testing file mode.

        >>> import stat
        >>> host.file("/etc/shadow").mode == stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP
        True

        .. _oct(x): https://docs.python.org/3/library/functions.html#oct
        .. _stat: https://docs.python.org/3/library/stat.html
        """  # noqa
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
            raise RuntimeError("Unexpected output {}".format(out))
        if decode:
            return out.stdout
        return out.stdout_bytes

    @property
    def content(self):
        """Return file content as bytes

        >>> host.file("/tmp/foo").content
        b'caf\\xc3\\xa9'
        """
        return self._get_content(False)

    @property
    def content_string(self):
        """Return file content as string

        >>> host.file("/tmp/foo").content_string
        'café'
        """
        return self._get_content(True)

    @property
    def mtime(self):
        """Return time of last modification as datetime.datetime object

        >>> host.file("/etc/passwd").mtime
        datetime.datetime(2015, 3, 15, 20, 25, 40)
        """
        raise NotImplementedError

    @property
    def size(self):
        """Return size of file in bytes"""
        raise NotImplementedError

    def listdir(self):
        """Return list of items under the directory

        >>> host.file("/tmp").listdir()
        ['foo_file', 'bar_dir']
        """
        out = self.run_test("ls -1 -q -- %s", self.path)
        if out.rc != 0:
            raise RuntimeError("Unexpected output {}".format(out))
        return out.stdout.splitlines()

    def __repr__(self):
        return "<file {}>".format(self.path)

    def __eq__(self, other):
        if isinstance(other, File):
            return self.path == other.path
        if isinstance(other, str):
            return self.path == other
        return False

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            return GNUFile
        if host.system_info.type == "netbsd":
            return NetBSDFile
        if host.system_info.type.endswith("bsd"):
            return BSDFile
        if host.system_info.type == "darwin":
            return DarwinFile
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
        return self.check_output("sha256sum %s | cut -d ' ' -f 1", self.path)


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
        return self.check_output("sha256 < %s", self.path)


class DarwinFile(BSDFile):
    @property
    def linked_to(self):
        link_script = """
        TARGET_FILE='{0}'
        cd `dirname $TARGET_FILE`
        TARGET_FILE=`basename $TARGET_FILE`
        while [ -L "$TARGET_FILE" ]
        do
            TARGET_FILE=`readlink $TARGET_FILE`
            cd `dirname $TARGET_FILE`
            TARGET_FILE=`basename $TARGET_FILE`
        done
        PHYS_DIR=`pwd -P`
        RESULT=$PHYS_DIR/$TARGET_FILE
        echo $RESULT
        """.format(
            self.path
        )
        return self.check_output(link_script)


class NetBSDFile(BSDFile):
    @property
    def sha256sum(self):
        return self.check_output("cksum -a sha256 < %s", self.path)
