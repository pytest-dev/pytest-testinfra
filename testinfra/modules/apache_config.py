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

from apacheconfig.lexer import make_lexer
from apacheconfig.parser import make_parser
from apacheconfig.loader import ApacheConfigLoader
from apacheconfig.error import ApacheConfigError


def create_utility_class(klass, _host):
    return type(klass.__name__, (klass,), {
        "_host": _host,
        "run": _host.run,
        "run_expect": _host.run_expect,
        "run_test": _host.run_test,
        "check_output": _host.check_output,
    })


class ApacheConfig(Module):
    """Exposes apache config options as a dict"""

    def __init__(self, path, **options):
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)
        remote_host = create_utility_class(RemoteHost, self._host)

        self.path = path
        self._config = None
        self._loader = ApacheConfigLoader(
            ApacheConfigParser(ApacheConfigLexer()), host=remote_host, **options)

        super(ApacheConfig, self).__init__()

    @property
    def config(self):
        if not self._config:
            self._config = self._loader.load(self.path)
        return self._config


class RemoteHost(object):
    """RemoteHost for ApacheConfigLoader"""

    def __init__(self):
        self._path = create_utility_class(Path, self._host)
        self._env = create_utility_class(Env, self._host)


        super(RemoteHost, self).__init__()

    @property
    def path(self):
        return self._path

    @property
    def env(self):
        return self._env

    def open(self, filename):
        out = self.run_test("cat -- %s", self.path)
        if out.rc != 0:
            raise IOError
        return out.stdout

class Path(object):

    def __init__(self):
        super(Path, self).__init__.py

    def isabs(filepath):
        self.run
