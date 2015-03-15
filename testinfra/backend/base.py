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

import collections
import pipes


CommandResult = collections.namedtuple('CommandResult', [
    'rc', 'stdout', 'stderr', 'command',
])


class BaseBackend(object):

    def quote(self, command, *args):
        return command % tuple(pipes.quote(a) for a in args)

    def run(self, command, *args):
        raise NotImplementedError
