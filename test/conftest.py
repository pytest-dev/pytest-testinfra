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

import itertools
import os
import subprocess
import sys
import threading
import time
import urllib.parse

import pytest

import testinfra
from testinfra.backend.base import BaseBackend
from testinfra.backend import parse_hostspec


BASETESTDIR = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.path.abspath(os.path.join(BASETESTDIR, os.pardir))
_HAS_DOCKER = None

# Use testinfra to get a handy function to run commands locally
local_host = testinfra.get_host('local://')
check_output = local_host.check_output


def has_docker():
    global _HAS_DOCKER
    if _HAS_DOCKER is None:
        _HAS_DOCKER = local_host.exists("docker")
    return _HAS_DOCKER


# Generated with
# $ echo myhostvar: bar > hostvars.yml
# $ echo polichinelle > vault-pass.txt
# $ ansible-vault encrypt --vault-password-file vault-pass.txt hostvars.yml
# $ cat hostvars.yml
ANSIBLE_HOSTVARS = """$ANSIBLE_VAULT;1.1;AES256
39396233323131393835363638373764336364323036313434306134636633353932623363646233
6436653132383662623364313438376662666135346266370a343934663431363661393363386633
64656261336662623036373036363535313964313538366533313334366363613435303066316639
3235393661656230350a326264356530326432393832353064363439393330616634633761393838
3261
"""

DOCKER_IMAGES = [
    "alpine",
    "archlinux",
    "centos_6",
    "centos_7",
    "debian_buster",
    "ubuntu_xenial",
]


def setup_ansible_config(tmpdir, name, host, user, port, key):
    items = [
        name,
        "ansible_ssh_private_key_file={}".format(key),
        'ansible_ssh_common_args="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=FATAL"',  # noqa
        "myvar=foo",
        "ansible_host={}".format(host),
        "ansible_user={}".format(user),
        "ansible_port={}".format(port),
    ]
    tmpdir.join("inventory").write(
        "[testgroup]\n" + " ".join(items) + "\n")
    tmpdir.mkdir("host_vars").join(name).write(ANSIBLE_HOSTVARS)
    tmpdir.mkdir("group_vars").join("testgroup").write((
        "---\n"
        "myhostvar: should_be_overriden\n"
        "mygroupvar: qux\n"
    ))
    vault_password_file = tmpdir.join("vault-pass.txt")
    vault_password_file.write("polichinelle\n")
    ansible_cfg = tmpdir.join("ansible.cfg")
    ansible_cfg.write((
        "[defaults]\n"
        "vault_password_file={}\n"
        "host_key_checking=False\n\n"
        "[ssh_connection]\n"
        "pipelining=True\n"
    ).format(str(vault_password_file)))


def build_docker_container_fixture(image, scope):
    @pytest.fixture(scope=scope)
    def func(request):
        docker_host = os.environ.get("DOCKER_HOST")
        if docker_host is not None:
            docker_host = urllib.parse.urlparse(
                docker_host).hostname or "localhost"
        else:
            docker_host = "localhost"

        cmd = ["docker", "run", "-d", "-P"]
        if image in DOCKER_IMAGES:
            cmd.append("--privileged")

        cmd.append("testinfra:" + image)
        docker_id = check_output(" ".join(cmd))

        def teardown():
            check_output("docker rm -f %s", docker_id)

        request.addfinalizer(teardown)

        port = check_output("docker port %s 22", docker_id)
        port = int(port.rsplit(":", 1)[-1])
        return docker_id, docker_host, port
    fname = "_docker_container_%s_%s" % (image, scope)
    mod = sys.modules[__name__]
    setattr(mod, fname, func)


def initialize_container_fixtures():
    for image, scope in itertools.product(
            DOCKER_IMAGES, ["function", "session"]):
        build_docker_container_fixture(image, scope)


initialize_container_fixtures()


@pytest.fixture
def host(request, tmpdir_factory):
    if not has_docker():
        pytest.skip()
        return
    image, kw = parse_hostspec(request.param)
    spec = BaseBackend.parse_hostspec(image)

    for marker in getattr(request.function, 'pytestmark', []):
        if marker.name == 'destructive':
            scope = "function"
            break
    else:
        scope = "session"

    fname = "_docker_container_%s_%s" % (spec.name, scope)
    docker_id, docker_host, port = request.getfixturevalue(fname)

    if kw["connection"] == "docker":
        hostname = docker_id
    elif kw["connection"] in ("ansible", "ssh", "paramiko", "safe-ssh"):
        hostname = spec.name
        tmpdir = tmpdir_factory.mktemp(str(id(request)))
        key = tmpdir.join("ssh_key")
        key.write(open(os.path.join(BASETESTDIR, "ssh_key")).read())
        key.chmod(384)  # octal 600
        if kw["connection"] == "ansible":
            setup_ansible_config(
                tmpdir, hostname, docker_host, spec.user or "root",
                port, str(key))
            os.environ["ANSIBLE_CONFIG"] = str(tmpdir.join("ansible.cfg"))
            # this force backend cache reloading
            kw["ansible_inventory"] = str(tmpdir.join("inventory"))
        else:
            ssh_config = tmpdir.join("ssh_config")
            ssh_config.write((
                "Host {}\n"
                "  Hostname {}\n"
                "  Port {}\n"
                "  UserKnownHostsFile /dev/null\n"
                "  StrictHostKeyChecking no\n"
                "  IdentityFile {}\n"
                "  IdentitiesOnly yes\n"
                "  LogLevel FATAL\n"
            ).format(hostname, docker_host, port, str(key)))
            kw["ssh_config"] = str(ssh_config)

        # Wait ssh to be up
        service = testinfra.get_host(
            docker_id, connection='docker').service

        images_with_sshd = (
            "centos_6",
            "centos_7",
            "alpine",
            "archlinux"
        )

        if image in images_with_sshd:
            service_name = "sshd"
        else:
            service_name = "ssh"

        while not service(service_name).is_running:
            time.sleep(.5)

    if kw["connection"] != "ansible":
        hostspec = (spec.user or "root") + "@" + hostname
    else:
        hostspec = spec.name

    b = testinfra.host.get_host(hostspec, **kw)
    b.backend.get_hostname = lambda: image
    return b


@pytest.fixture
def docker_image(host):
    return host.backend.get_hostname()


def pytest_generate_tests(metafunc):
    if "host" in metafunc.fixturenames:
        for marker in getattr(metafunc.function, 'pytestmark', []):
            if marker.name == 'testinfra_hosts':
                hosts = marker.args
                break
        else:
            # Default
            hosts = ["docker://debian_buster"]
        metafunc.parametrize("host", hosts, indirect=True,
                             scope="function")


def pytest_configure(config):
    if not has_docker():
        return

    def build_image(build_failed, dockerfile, image, image_path):
        try:
            subprocess.check_call([
                "docker", "build", "-f", dockerfile,
                "-t", "testinfra:{0}".format(image),
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

    config.addinivalue_line(
        "markers",
        "testinfra_hosts(host_selector): mark test to run on selected hosts"
    )
    config.addinivalue_line(
        "markers",
        "destructive: mark test as destructive"
    )
