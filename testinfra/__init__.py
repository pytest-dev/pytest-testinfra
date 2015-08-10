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

from testinfra import backend

__all__ = ["get_backend"]


_BACKEND_CACHE = {}


def get_backend(backend_type, *args, **kwargs):
    key = (backend_type, args)
    if key not in _BACKEND_CACHE:
        _BACKEND_CACHE[key] = backend.get_backend(
            backend_type, *args, **kwargs)
    return _BACKEND_CACHE[key]
