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
import pytest

pytestmark = pytest.mark.testinfra_hosts(
    "ssh://debian_jessie",
    "ssh://debian_jessie?sudo=True",
    "safe-ssh://debian_jessie",
    "paramiko://debian_jessie",
    "ansible://debian_jessie",
)


def test_command(Command):
    assert Command.check_output("true") == ""
    assert Command("echo a b | grep -q %s", "a c").rc == 1


def test_encoding(TestinfraBackend, Command):
    if TestinfraBackend.get_connection_type() == "ansible":
        pytest.skip("ansible handle encoding himself")

    # jessie image is fr_FR@ISO-8859-15
    cmd = Command("ls -l %s", "/é")
    if TestinfraBackend.get_connection_type() == "docker":
        # docker bug ?
        assert cmd.stderr_bytes == (
            b"ls: impossible d'acc\xe9der \xe0 /\xef\xbf\xbd: "
            b"Aucun fichier ou dossier de ce type\n"
        )
    else:
        assert cmd.stderr_bytes == (
            b"ls: impossible d'acc\xe9der \xe0 /\xe9: "
            b"Aucun fichier ou dossier de ce type\n"
        )
        assert cmd.stderr == (
            "ls: impossible d'accéder à /é: "
            "Aucun fichier ou dossier de ce type\n"
        )
