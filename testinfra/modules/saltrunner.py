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

from __future__ import unicode_literals


import json

import six

from testinfra.modules.base import InstanceModule


class SaltRunner(InstanceModule):
    """Run salt module functions


    >>> host.salt_run("manage.up", "")
    '1.6.2-5'
    >>> host.salt_run("pkg.version", ["nginx", "php5-fpm"])
    {'nginx': '1.6.2-5', 'php5-fpm': '5.6.7+dfsg-1'}
    >>> host.salt_run("grains.item", ["osarch", "mem_total", "num_cpus"])
    {'osarch': 'amd64', 'num_cpus': 4, 'mem_total': 15520}

    Run ``salt-run sys.doc`` to get a complete list of functions
    """

    def __call__(self, fnct, config=None, *args, **kwargs):
        args = args or []
        if isinstance(args, six.string_types):
            args = [args]
        if self._host.backend.HAS_RUN_SALT:
            return self._host.backend.salt_runner(
                fnct, *args, **kwargs)["stdout"]
        else:
            cmd_args = []
            cmd = "salt-run --out=json"
            if config is not None:
                cmd += " -c %s"
                cmd_args.append(config)
            cmd += " %s" + len(args) * " %s"
            cmd_args += [fnct] + args
            return json.loads(self.check_output(cmd, *cmd_args))

    def __repr__(self):
        return "<salt_runner>"
