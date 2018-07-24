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

import io
import os

from apacheconfig.lexer import make_lexer
from apacheconfig.parser import make_parser
from apacheconfig.loader import ApacheConfigLoader
from apacheconfig.error import ApacheConfigError


class ApacheConfig(Module):
    """Exposes apache config options as a dict"""

    def __init__(self, path, **options):
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)
        remote_host = TestInfraHostReader(self._host)

        self._loader = ApacheConfigLoader(
            ApacheConfigParser(ApacheConfigLexer()), host=remote_host, **options)

        super(ApacheConfig, self).__init__()

    @property
    def config(self):
        if not self._config:
            self._config = self._loader.load(self.path)
        return self._config


class TestInfraHostReader(object):
    """RemoteHost for ApacheConfigLoader"""

    def __init__(self, host):
        self._host = host
        self._env = host.env();

        super(RemoteHost, self).__init__()

    @property
    def env(self):
        return self._env

    def exists(self, filepath):
        return self._host.run_test("test -f %s", filepath).rc == 0

    def isdir(self, filepath):
        return self._host.run_test("test -d %s" % filepath).rc == 0

    def listdir(self, filepath):
        out = self._host.run_test("ls -A %s" filepath)
        if out.rc != 0:
            raise OSError
        else:
            return out.stdout.split()

    def open(self, filepath):
        out = self.run_test("cat -- %s", filepath)
        if out.rc != 0:
            raise IOError
        return io.StringIO(out.stdout)

