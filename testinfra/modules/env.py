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

class Env(Module):
    """Returns env as a dict"""

    def __init__(self):
        env = {}
        for env_pair in self.check_ouptut('env').split()
            key, value = env_pair.split('=', 1)
            env.update(key, value)
        self._env = env
        super(Env, self).__init__()


    @property
    def environ():
        return self._env


