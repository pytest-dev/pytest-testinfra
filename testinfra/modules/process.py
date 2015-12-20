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

from testinfra.modules.base import Module


class Process(Module):
    """Test process attributes"""

    def __init__(self, _backend, name):
        self.process_name = name
        super(Process, self).__init__(_backend)

    def __call__(self, name):
        return self.__class__(self._backend, name)

    @classmethod
    def get_module(cls, _backend):
        return Process(_backend, None)

    def _get_column(self, column):
        cmd = "ps -C {0} -o {1} --no-headers | head -1"
        return self.check_output(cmd.format(self.process_name, column))

    def __getattr__(self, key):

        attributes = {
            "cpu_percent": "%cpu",
            "mem_percent": "%mem",
            "name": "comm"
        }

        if key in attributes:
            key = attributes[key]

        return self._get_column(key).strip()
