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
from testinfra.backend import paramiko
from testinfra.backend import ssh


def get_backend(backend_type, *args, **kwargs):
    try:
        backend_class = {
            "local": local.LocalBackend,
            "ssh": ssh.SshBackend,
            "safe_ssh": ssh.SafeSshBackend,
            "paramiko": paramiko.ParamikoBakend,
        }[backend_type]
    except KeyError:
        raise RuntimeError("Unknown backend '%s'" % (backend_type,))
    return backend_class(*args, **kwargs)
