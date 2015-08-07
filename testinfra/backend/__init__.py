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

import importlib


def get_backend(backend_type, *args, **kwargs):

    backend_type_split = backend_type.split(".")
    try:
        if len(backend_type_split) == 1:
            backend_module = importlib.import_module("testinfra.backend.%s" %
                                                     backend_type)
            backend_class = backend_module.Backend
        else:
            backend_module = importlib.import_module(".".join(
                                                     backend_type_split[:-1]))
            backend_class = getattr(backend_module, backend_type_split[-1])

    except ImportError:
        raise RuntimeError("Unknown backend '%s'" % (backend_type,))
    return backend_class(*args, **kwargs)
