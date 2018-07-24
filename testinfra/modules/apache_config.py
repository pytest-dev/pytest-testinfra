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

from testinfra.modules.base import Module
from apacheconfig.lexer import make_lexer
from apacheconfig.parser import make_parser
from apacheconfig.loader import ApacheConfigLoader
from apacheconfig.reader import TestInfraHostReader


class ApacheConfig(Module):
    """Exposes apache configuration as a dict"""

    def __init__(self, path, **options):
        self._path = path
        self._config = None

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)
        remote_host = TestInfraHostReader(self._host)

        self._loader = ApacheConfigLoader(
            ApacheConfigParser(ApacheConfigLexer()), host=remote_host, **options)

        super(ApacheConfig, self).__init__()

    @property
    def config(self):
        if not self._config:
            self._config = self._loader.load(self._path)
        return self._config

    @property
    def path(self):
        return self._path
