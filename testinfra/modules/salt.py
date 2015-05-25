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


import json

import pytest
import six

from testinfra import get_backend
from testinfra.modules.base import Module


class Salt(Module):
    """Wrapper to 'salt-call'

    >>> Salt("pkg.version", "nginx")
    '1.6.2-5'

    >>> Salt("pkg.version", ["nginx", "php5-fpm"])
    {'nginx': '1.6.2-5', 'php5-fpm': '5.6.7+dfsg-1'}

    >>> Salt("grains.item", ["osarch", "mem_total", "num_cpus"])
    {'osarch': 'amd64', 'num_cpus': 4, 'mem_total': 15520}
    """

    def __call__(self, func, args=None):
        args = args or []
        if isinstance(args, six.string_types):
            args = [args]
        backend = get_backend()
        if backend.get_backend_type() == "salt":
            return backend.run_salt(func, args)
        else:
            cmd = "salt-call --local --out=json %s" + len(args) * " %s"
            cmd_args = [func] + args
            return json.loads(self.check_output(cmd, *cmd_args))["local"]

    def __repr__(self):
        return "<salt>"

    @classmethod
    def as_fixture(cls):
        @pytest.fixture(scope="module")
        def f(testinfra_backend):
            return Salt()
        f.__doc__ = cls.__doc__
        return f
