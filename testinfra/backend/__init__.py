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

from six.moves import urllib

from testinfra.backend import ansible
from testinfra.backend import docker
from testinfra.backend import local
from testinfra.backend import paramiko
from testinfra.backend import salt
from testinfra.backend import ssh

BACKENDS = dict((klass.get_connection_type(), klass) for klass in (
    local.LocalBackend,
    ssh.SshBackend,
    ssh.SafeSshBackend,
    paramiko.ParamikoBackend,
    salt.SaltBackend,
    docker.DockerBackend,
    ansible.AnsibleBackend,
))


def get_backend_class(connection):
    try:
        return BACKENDS[connection]
    except KeyError:
        raise RuntimeError("Unknown connection type '%s'" % (connection,))


def parse_hostspec(hostspec):
    kw = {}
    if hostspec is not None and "://" in hostspec:
        url = urllib.parse.urlparse(hostspec)
        kw["connection"] = url.scheme
        host = url.netloc
        query = urllib.parse.parse_qs(url.query)
        if query.get("sudo", ["false"])[0].lower() == "true":
            kw["sudo"] = True
        for key in (
            "ssh_config", "ansible_inventory",
        ):
            if key in query:
                kw[key] = query.get(key)[0]
    else:
        host = hostspec
    return host, kw


def get_backend(hostspec, **kwargs):
    host, kw = parse_hostspec(hostspec)
    for k, v in kwargs.items():
        kw.setdefault(k, v)
    kw.setdefault("connection", "paramiko")
    klass = get_backend_class(kw["connection"])
    if kw["connection"] == "local":
        return klass(**kw)
    else:
        return klass(host, **kw)


def get_backends(hosts, **kwargs):
    backends = []
    for hostspec in hosts:
        host, kw = parse_hostspec(hostspec)
        for k, v in kwargs.items():
            kw.setdefault(k, v)
        connection = kw.get("connection")
        if host is None and connection is None:
            connection = "local"
        elif host is not None and connection is None:
            connection = "paramiko"
        klass = get_backend_class(connection)
        for name in klass.get_hosts(host, **kw):
            if connection == "local":
                backends.append(klass(**kw))
            else:
                backends.append(klass(name, **kw))
    return backends
