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

import logging
import subprocess
from testinfra.backend import base

logger = logging.getLogger("testinfra.backend")


class Backend(base.BaseBackend):
    _backend_type = "local"

    def __init__(self, sudo=False, *args, **kwargs):
        self.sudo = sudo
        super(Backend, self).__init__(*args, **kwargs)

    def run(self, command, *args, **kwargs):
        if self.sudo:
            command = "sudo " + command
        command = self.quote(command, *args)
        logger.info("RUN %s", command)
        command = self.encode(command)
        p = subprocess.Popen(
            command, shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        return base.CommandResult(
            self, p.returncode, stdout, stderr, command,
        )
