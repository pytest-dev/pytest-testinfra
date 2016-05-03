# coding: utf-8
# Copyright © 2016 Philippe Pepiot <phil@philpep.org>
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
from __future__ import print_function

import os
import subprocess
import threading
import time

import pytest
from six.moves import urllib

try:
    import ansible
except ImportError:
    ansible = None

import testinfra
from testinfra.backend.base import BaseBackend
from testinfra.backend import parse_hostspec


BASETESTDIR = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.path.abspath(os.path.join(BASETESTDIR, os.pardir, os.pardir))

# Use testinfra to get a handy function to run commands locally
_Command = testinfra.get_backend("local://").get_module("Command")
check_output = _Command.check_output


def get_ansible_inventory(name, hostname, user, port, key):
    ansible_major_version = int(ansible.__version__.split(".", 1)[0])
    items = [
        name,
        "ansible_ssh_private_key_file={}".format(key),
    ]
    if ansible_major_version == 1:
        items.extend([
            "ansible_ssh_host={}".format(hostname),
            "ansible_ssh_user={}".format(user),
            "ansible_ssh_port={}".format(port),
        ])
    elif ansible_major_version == 2:
        items.extend([
            "ansible_host={}".format(hostname),
            "ansible_user={}".format(user),
            "ansible_port={}".format(port),
        ])
    return " ".join(items) + "\n"


def start_container(request, image, tmpdir):
    docker_host = os.environ.get("DOCKER_HOST")
    if docker_host is not None:
        docker_host = urllib.parse.urlparse(
            docker_host).hostname or "localhost"
    else:
        docker_host = "localhost"

    cmd = ["docker", "run", "-d", "-P"]
    if image in ("debian_jessie", "centos_7", "fedora"):
        cmd.append("--privileged")

    cmd.append("philpep/testinfra:" + image)
    docker_id = check_output(" ".join(cmd))

    def teardown():
        check_output("docker rm -f %s", docker_id)

    request.addfinalizer(teardown)

    port = check_output("docker port %s 22", docker_id)
    port = int(port.rsplit(":", 1)[-1])
    return docker_id, docker_host, port


@pytest.fixture
def TestinfraBackend(request, tmpdir_factory):
    image, kw = parse_hostspec(request.param)
    docker_id, docker_host, port = start_container(
        request, image, tmpdir_factory)

    if kw["connection"] == "docker":
        host = docker_id
    elif kw["connection"] in ("ansible", "ssh", "paramiko", "safe-ssh"):
        host, user, _ = BaseBackend.parse_hostspec(image)
        tmpdir = tmpdir_factory.mktemp(str(id(request)))
        key = tmpdir.join("ssh_key")
        key.write(open(os.path.join(BASETESTDIR, "ssh_key")).read())
        key.chmod(384)  # octal 600
        if kw["connection"] == "ansible":
            if ansible is None:
                pytest.skip()
                return
            inventory = tmpdir.join("inventory")
            inventory.write(get_ansible_inventory(
                host, docker_host, user or "root", port, str(key)))
            kw["ansible_inventory"] = str(inventory)
        else:
            ssh_config = tmpdir.join("ssh_config")
            ssh_config.write((
                "Host {}\n"
                "  Hostname {}\n"
                "  User {}\n"
                "  Port {}\n"
                "  UserKnownHostsFile /dev/null\n"
                "  StrictHostKeyChecking no\n"
                "  IdentityFile {}\n"
                "  IdentitiesOnly yes\n"
                "  LogLevel FATAL\n"
            ).format(image, docker_host, user or "root", port, str(key)))
            kw["ssh_config"] = str(ssh_config)

        # Wait ssh to be up
        service = testinfra.get_backend(
            docker_id, connection="docker"
        ).get_module("Service")

        while not service("ssh").is_running:
            time.sleep(.5)

    backend = testinfra.get_backend(host, **kw)
    backend.get_hostname = lambda: image
    return backend


@pytest.fixture
def docker_image(TestinfraBackend):
    return TestinfraBackend.get_hostname()


def pytest_generate_tests(metafunc):
    if "TestinfraBackend" in metafunc.fixturenames:
        marker = getattr(metafunc.function, "testinfra_hosts", None)
        if marker is not None:
            hosts = marker.args
        else:
            # Default
            hosts = ["docker://debian_jessie"]

        if getattr(metafunc.function, "destructive", None) is not None:
            scope = "function"
        else:
            scope = "session"

        metafunc.parametrize(
            "TestinfraBackend", hosts, indirect=True, scope=scope)


def pytest_configure(config):
    def build_image(build_failed, dockerfile, image, image_path):
        print("BUILD", image)
        try:
            subprocess.check_call([
                "docker", "build", "-f", dockerfile,
                "-t", "philpep/testinfra:{0}".format(image),
                image_path])
        except Exception:
            build_failed.set()
            raise

    threads = []
    images_path = os.path.join(BASEDIR, "images")
    build_failed = threading.Event()
    for image in os.listdir(images_path):
        image_path = os.path.join(images_path, image)
        dockerfile = os.path.join(image_path, "Dockerfile")
        if os.path.exists(dockerfile):
            threads.append(threading.Thread(target=build_image, args=(
                build_failed, dockerfile, image, image_path)))

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    if build_failed.is_set():
        raise RuntimeError("One or more docker build failed")
