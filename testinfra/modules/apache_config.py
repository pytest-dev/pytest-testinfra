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

from testinfra.modules.base import Module
from apacheconfig.lexer import make_lexer
from apacheconfig.parser import make_parser
from apacheconfig.loader import ApacheConfigLoader


class ApacheConfig(Module):
    """Exposes apache configuration as a dict"""

    def __init__(self, path, **options):
        self._path = path
        self._config = None

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)
        remote_reader = CachedTestInfraHostReader(self._host)

        self._loader = ApacheConfigLoader(
            ApacheConfigParser(ApacheConfigLexer()), reader=remote_reader, **options)

        super(ApacheConfig, self).__init__()

    @property
    def config(self):
        if not self._config:
            self._config = self._loader.load(self._path)
        return self._config

    @property
    def path(self):
        return self._path


class TestInfraHostReader(object):
    """TestInfraHostReader for ApacheConfigLoader"""

    def __init__(self, host):
        self._host = host
        self._environ = host.env().environ

    @property
    def environ(self):
        return self._environ

    def exists(self, filepath):
        return self._host.run_test("test -f %s", filepath).rc == 0

    def isdir(self, filepath):
        return self._host.run_test("test -d %s" % filepath).rc == 0

    def listdir(self, filepath):
        out = self._host.run_test("ls -A %s" % filepath)
        if out.rc != 0:
            raise OSError
        else:
            return out.stdout.split()

    def open(self, filepath):
        out = self._host.run_test("cat -- %s", filepath)
        if out.rc != 0:
            raise IOError
        return io.StringIO(out.stdout)

class CachedTestInfraHostReader(TestInfraHostReader):

    def __init__(self, host):
        self._cache = {}
        super(CachedTestInfraHostReader, self).__init__(host)

    def open(self, filepath):
        if not filepath in self._cache:
            out = self._host.run_test("cat -- %s", filepath)
            if out.rc != 0:
                raise IOError
            self._cache[filepath] = out.stdout
        return io.StringIO(self._cache[filepath])
