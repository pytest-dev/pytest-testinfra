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

import importlib
import os
import urllib.parse

BACKENDS = {
    "local": "testinfra.backend.local.LocalBackend",
    "ssh": "testinfra.backend.ssh.SshBackend",
    "safe-ssh": "testinfra.backend.ssh.SafeSshBackend",
    "paramiko": "testinfra.backend.paramiko.ParamikoBackend",
    "salt": "testinfra.backend.salt.SaltBackend",
    "docker": "testinfra.backend.docker.DockerBackend",
    "podman": "testinfra.backend.podman.PodmanBackend",
    "ansible": "testinfra.backend.ansible.AnsibleBackend",
    "kubectl": "testinfra.backend.kubectl.KubectlBackend",
    "winrm": "testinfra.backend.winrm.WinRMBackend",
    "lxc": "testinfra.backend.lxc.LxcBackend",
    "openshift": "testinfra.backend.openshift.OpenShiftBackend",
}


def get_backend_class(connection):
    try:
        classpath = BACKENDS[connection]
    except KeyError:
        raise RuntimeError("Unknown connection type '{}'".format(connection))
    module, name = classpath.rsplit(".", 1)
    return getattr(importlib.import_module(module), name)


def parse_hostspec(hostspec):
    kw = {}
    if hostspec is not None and "://" in hostspec:
        url = urllib.parse.urlparse(hostspec)
        kw["connection"] = url.scheme
        host = url.netloc
        query = urllib.parse.parse_qs(url.query)
        for key in ("sudo", "ssl", "no_ssl", "no_verify_ssl", "force_ansible"):
            if query.get(key, ["false"])[0].lower() == "true":
                kw[key] = True
        for key in (
            "sudo_user",
            "namespace",
            "container",
            "read_timeout_sec",
            "operation_timeout_sec",
            "timeout",
            "controlpersist",
            "kubeconfig",
            "context",
        ):
            if key in query:
                kw[key] = query[key][0]
        for key in (
            "ssh_config",
            "ansible_inventory",
            "ssh_identity_file",
        ):
            if key in query:
                kw[key] = os.path.expanduser(query[key][0])
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
    return klass(host, **kw)


def get_backends(hosts, **kwargs):
    backends = {}
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
            key = (name, frozenset(kw.items()))
            if key in backends:
                continue
            if connection == "local":
                backend = klass(**kw)
            else:
                backend = klass(name, **kw)
            backends[key] = backend
    return list(backends.values())
