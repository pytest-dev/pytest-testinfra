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

from six.moves import urllib

from testinfra.backend import docker
from testinfra.backend import local
from testinfra.backend import paramiko
from testinfra.backend import salt
from testinfra.backend import ssh

BACKENDS = dict((name, klass) for name, klass in (
    ("local", local.LocalBackend),
    ("ssh", ssh.SshBackend),
    ("safe-ssh", ssh.SafeSshBackend),
    ("paramiko", paramiko.ParamikoBackend),
    ("salt", salt.SaltBackend),
    ("docker", docker.DockerBackend),
))


def get_backend(hostspec, connection="paramiko://", **kwargs):
    kw = kwargs.copy()
    if "://" in hostspec:
        url = urllib.parse.urlparse(hostspec)
        connection = url.scheme
        host = url.netloc
        query = urllib.parse.parse_qs(url.query)
        if query.get("sudo", ["false"])[0].lower() == "true":
            kw["sudo"] = True
        if "ssh_config" in query:
            kw["ssh_config"] = query.get("ssh_config")[0]
    else:
        host = hostspec
    try:
        klass = BACKENDS[connection]
    except KeyError:
        raise RuntimeError("Unknown connection type '%s'" % (connection,))
    if connection == "local":
        return klass(**kw)
    else:
        return klass(host, **kw)
