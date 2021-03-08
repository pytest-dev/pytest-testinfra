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

import contextlib

from testinfra.modules.base import InstanceModule


class Sudo(InstanceModule):
    """Sudo module allow to run certain portion of code under another user.

    It is used as a context manager and can be nested.

    >>> Command.check_output("whoami")
    'phil'
    >>> with host.sudo():
    ...     host.check_output("whoami")
    ...     with host.sudo("www-data"):
    ...         host.check_output("whoami")
    ...
    'root'
    'www-data'

    """

    @contextlib.contextmanager
    def __call__(self, user=None):
        old_get_command = self._host.backend.get_command
        quote = self._host.backend.quote
        get_sudo_command = self._host.backend.get_sudo_command

        def get_command(command, *args):
            return old_get_command(get_sudo_command(quote(command, *args), user))

        self._host.backend.get_command = get_command
        try:
            yield
        finally:
            self._host.backend.get_command = old_get_command

    def __repr__(self):
        return "<sudo>"
