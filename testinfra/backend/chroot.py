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
import os.path
from typing import Any

from testinfra.backend import base


class ChrootBackend(base.BaseBackend):
    """Run commands in a chroot folder

    Requires root access or sudo
    Can be invoked by --hosts=/path/to/chroot/ --connection=chroot --sudo
    """

    NAME = "chroot"

    def __init__(self, name: str, *args: Any, **kwargs: Any):
        self.name = name
        super().__init__(self.name, *args, **kwargs)

    def run(self, command: str, *args: str, **kwargs: Any) -> base.CommandResult:
        if not os.path.exists(self.name) and os.path.isdir(self.name):
            raise RuntimeError(
                "chroot path {} not found or not a directory".format(self.name)
            )
        cmd = self.get_command(command, *args)
        out = self.run_local("chroot %s /bin/sh -c %s", self.name, cmd)
        out.command = self.encode(cmd)
        return out
