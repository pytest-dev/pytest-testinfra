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

from testinfra.backend import local


class SshBackend(local.LocalBackend):

    def __init__(self, host, user="root", *args, **kwargs):
        self.host = host
        self.user = user
        super(SshBackend, self).__init__(*args, **kwargs)

    def run(self, command, *args, **kwargs):
        return super(SshBackend, self).run(
            "ssh %s@%s %s", self.user, self.host,
            self.quote(command, *args),
            **kwargs)
