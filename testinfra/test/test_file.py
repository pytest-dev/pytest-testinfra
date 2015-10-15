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

import os


def test_file(remote_tempdir, Command, SystemInfo, File):
    filename = os.path.join(remote_tempdir, "f")
    uid, gid = SystemInfo.uid, SystemInfo.gid
    user, group = SystemInfo.user, SystemInfo.group
    assert Command(
        "printf foo > %s && chmod 600 %s && chown %s:%s %s",
        filename, filename, user, group, filename).rc == 0
    f = File(filename)
    assert f.exists
    assert f.is_file
    assert f.content == b"foo"
    assert f.content_string == "foo"
    assert f.user == user
    assert f.uid == uid
    assert f.gid == gid
    assert f.group == group
    assert f.mode == 0o600
    assert f.contains("fo")
    assert not f.is_directory
    assert not f.is_symlink
    assert not f.is_pipe
    assert f.linked_to == filename
    assert f.size == 3
    assert f.md5sum == "acbd18db4cc2f85cedef654fccc4a4d8"
    assert f.sha256sum == (
        "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
    )


def test_link(remote_tempdir, Command, File):
    orig = os.path.join(remote_tempdir, "f")
    link = os.path.join(remote_tempdir, "l")
    Command("touch %s", orig)
    assert Command("ln -fsn %s %s", orig, link).rc == 0
    l = File(link)
    assert l.is_symlink
    assert l.is_file
    assert l.linked_to == orig


def test_directory(remote_tempdir, File):
    f = File(remote_tempdir)
    assert f.is_directory
    assert not f.is_file


def test_pipe(remote_tempdir, Command, File):
    filename = os.path.join(remote_tempdir, "f")
    assert Command("mkfifo %s", filename).rc == 0
    assert File(filename).is_pipe


def test_empty_command_output(Command):
    assert Command.check_output("printf ''") == ""


def test_local_command(LocalCommand):
    assert LocalCommand.check_output("true") == ""
