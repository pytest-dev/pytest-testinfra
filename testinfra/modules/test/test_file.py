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
import grp
import os
import pwd
import six

from testinfra.modules import Command
from testinfra.modules import File


def test_file_content(mock_subprocess):
    content = b"".join([six.int2byte(x) for x in range(255)])
    mock_subprocess().configure_mock(**{
        "communicate.return_value": (content, b""),
        "returncode": 0,
    })
    assert File("/foo").content == content


def test_file(tmpdir):
    path = tmpdir.join("f")
    path.write(b"foo")
    path.chmod(0o600)
    f = File(path.strpath)
    pw = pwd.getpwuid(os.getuid())
    assert f.exists
    assert f.is_file
    assert f.content == b"foo"
    assert f.content_string == "foo"
    assert f.user == pw.pw_name
    assert f.uid == pw.pw_uid
    assert f.gid == pw.pw_gid
    assert f.group == grp.getgrgid(pw.pw_gid).gr_name
    assert f.mode == 600
    assert f.contains("fo")
    assert not f.is_directory
    assert not f.is_symlink
    assert not f.is_pipe
    assert f.linked_to == path.strpath
    assert f.size == 3
    assert f.md5sum == "acbd18db4cc2f85cedef654fccc4a4d8"
    assert f.sha256sum == (
        "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
    )
    assert f.mtime == datetime.datetime.fromtimestamp(
        path.mtime()).replace(microsecond=0)


def test_link(tmpdir):
    tmpdir.ensure("f")
    tmpdir.join("l").mksymlinkto(tmpdir.join("f"))
    l = File(tmpdir.join("l").strpath)
    assert l.is_symlink
    assert l.is_file
    assert l.linked_to == tmpdir.join("f").strpath


def test_directory(tmpdir):
    f = File(tmpdir.mkdir("sub").strpath)
    assert f.is_directory
    assert not f.is_file


def test_pipe(tmpdir):
    assert Command("mkfifo %s", tmpdir.join("f").strpath).rc == 0
    f = File(tmpdir.join("f").strpath)
    assert f.is_pipe
