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

from testinfra import backend

__all__ = ["get_backend", "get_backends"]


_BACKEND_CACHE = {}
_BACKENDS_CACHE = {}


def get_backend(hostspec, **kwargs):
    key = (hostspec, frozenset(kwargs.items()))
    if key not in _BACKEND_CACHE:
        _BACKEND_CACHE[key] = backend.get_backend(hostspec, **kwargs)
    return _BACKEND_CACHE[key]


def get_backends(hosts, **kwargs):
    key = (frozenset(hosts), frozenset(kwargs.items()))
    if key not in _BACKENDS_CACHE:
        _BACKENDS_CACHE[key] = backend.get_backends(hosts, **kwargs)
    return _BACKENDS_CACHE[key]
