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
from __future__ import print_function

import itertools
import mock
import os
import pytest
import subprocess
import sys
import threading
import time
import yaml

from six.moves import urllib
from testinfra.backend.base import CommandResult


try:
    import ansible
except ImportError:
    ansible = None

import testinfra
from testinfra.backend.base import BaseBackend
from testinfra.backend import parse_hostspec
from testinfra.utils.timed_thread import TimedThread


BASETESTDIR = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.path.abspath(os.path.join(BASETESTDIR, os.pardir))
_HAS_DOCKER = None
_HAS_VAGRANT = None

# Use testinfra to get a handy function to run commands locally
local_host = testinfra.get_host('local://')
check_output = local_host.check_output


def has_docker():
    global _HAS_DOCKER
    if _HAS_DOCKER is None:
        _HAS_DOCKER = local_host.exists("docker")
    return _HAS_DOCKER


def has_vagrant():
    global _HAS_VAGRANT
    if _HAS_VAGRANT is None:
        _HAS_VAGRANT = local_host.exists('vagrant')
    return _HAS_VAGRANT


def get_travisyml():
    fname = BASEDIR + '/.travis.yml'
    if os.path.isfile(fname):
        return os.path.abspath(fname)


def get_travis_install_helper():
    fname = BASEDIR + '/.travis/install.sh'
    if os.path.isfile(fname):
        return os.path.abspath(fname)

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


def setup_ansible_config(tmpdir, name, host, user, port, key):
    ansible_major_version = int(ansible.__version__.split(".", 1)[0])
    items = [
        name,
        "ansible_ssh_private_key_file={}".format(key),
        "myvar=foo",
    ]
    if ansible_major_version == 1:
        items.extend([
            "ansible_ssh_host={}".format(host),
            "ansible_ssh_user={}".format(user),
            "ansible_ssh_port={}".format(port),
        ])
    elif ansible_major_version == 2:
        items.extend([
            "ansible_host={}".format(host),
            "ansible_user={}".format(user),
            "ansible_port={}".format(port),
        ])
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


def vagrant_travis_helper(vagrant):
    travis_yml = get_travisyml()
    if travis_yml:
        with open(travis_yml, 'r') as ymlfd:
            yml = yaml.load(ymlfd)

        sut_dir = os.path.dirname(vagrant.vagrantfile)
        travis_helper = sut_dir + '/travis-helper.sh'

        with open(travis_helper, 'w') as fd:
            fd.write('#!/bin/bash\n\n# travis before_install scripts\n')

            before_install = yml.get('before_install')
            if before_install:
                [fd.write(item + '\n') for item in before_install]

            install_script = yml.get('install')
            if install_script:
                fd.write('\n\n# travis install scripts\n')
                for item in install_script:
                    if os.path.isfile(item):
                        with open(item, 'r') as script_fd:
                            script = script_fd.read()
                            fd.write(script + '\n')
                    else:
                        fd.write(item + '\n')
        os.chmod(travis_helper, 493)  # 0755 oct
        return True


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
        if image in ("ubuntu_xenial", "debian_jessie", "centos_6", "centos_7", "fedora"):
            cmd.append("--privileged")

        cmd.append("philpep/testinfra:" + image)
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
    for image, scope in itertools.product([
        "debian_jessie", "debian_wheezy", "ubuntu_trusty", "ubuntu_xenial",
        "fedora", "centos_6", "centos_7",
    ], ["function", "session"]):
        build_docker_container_fixture(image, scope)


initialize_container_fixtures()


def build_generic_ssh_config(host, hostname, user, port, priv_key):
    generic_ssh_config = (
        "Host {}\n"
        "  HostName {}\n"
        "  User {}\n"
        "  Port {}\n"
        "  UserKnownHostsFile /dev/null\n"
        "  StrictHostKeyChecking no\n"
        "  PasswordAuthentication no\n"
        "  IdentityFile {}\n"
        "  IdentitiesOnly yes\n"
        "  LogLevel FATAL\n"
    ).format(host, hostname, user, port, str(priv_key))
    return generic_ssh_config


@pytest.fixture
def build_ssh_config(request, tmpdir_factory):
    def on_call(*args, **kwargs):
        tmpdir = tmpdir_factory.mktemp(str(id(request)))
        key = tmpdir.join("ssh_key")
        key.write(open(os.path.join(BASETESTDIR, "ssh_key")).read())
        key.chmod(384)  # octal 600
        return build_generic_ssh_config(*args, priv_key=key, **kwargs)
    return on_call


@pytest.fixture
def vagrant_sut(request):

    if not has_vagrant():
        pytest.skip('Skipping test because vagrant is not installed')
        return

    def on_call(start=True, keep_running=True, args=(), kwargs={}):
        image, kw = testinfra.backend.parse_hostspec(request.param)
        vagrant = testinfra.get_host(image, **kw).backend

        vagrant_travis_helper(vagrant)

        # refresh status cache
        vagrant.status

        if start and vagrant.status.is_not_running:
            vagrant.up

        if start is False and vagrant.status.is_running:
            vagrant.suspend

        def build_box(vagrant):
            if vagrant.status.is_not_created:
                # invoke our pre-init script to do initial
                # provisioning to make tests run faster
                pre_init = vagrant.run('./pre-init')
                assert pre_init.rc == 0, './pre-init for vagrantfile={} has failed'.format(vagrant.vagrantfile)

        def teardown():
            if not keep_running:
                if vagrant.status.is_created:
                    vagrant.suspend

            if vagrant.status.is_not_created:
                TimedThread(target=build_box, join=True,
                            timeout=1800, args=(vagrant,)
                            )

            if keep_running and vagrant.status.is_not_running:
                vagrant.up

        request.addfinalizer(teardown)

        return vagrant
    return on_call


@pytest.fixture
def mock_vagrant_backend(request, monkeypatch, tmpdir):
    def on_call(method, hostspec='vagrant@default', vagrantfile='./Vagrantfile', *args, **kwargs):

        my_tmpdir = tmpdir.join('Vagrantfile')
        content = """

Vagrant.configure("2") do |config|
  config.vm.box = "centos/7"
end

"""
        vagrantfile = str(my_tmpdir)
        if os.path.isfile(vagrantfile):
            with open(vagrantfile, 'r') as fd:
                content = fd.read()

        my_tmpdir.write(content)
        host = testinfra.get_host(hostspec, connection='vagrant', vagrantfile=vagrantfile).backend

        def mocked_has_vagrant(*args):
            # simulate self.run_local('type vagrant').rc == 0
            if 'type vagrant' in args:
                mocked_result = mock.MagicMock(spec=CommandResult, rc=0)
                mocked_result.return_value.rc = 0
                return mocked_result
            return mock.MagicMock(spec=CommandResult)

        monkeypatch.setattr(host, 'run_local', mocked_has_vagrant)

        patcher = mock.patch.object(host, method, **kwargs)
        mocked_method = patcher.start()

        def teardown():
            teardown.patcher.stop()

        teardown.patcher = patcher
        teardown.mocked_method = mocked_method

        # add teardown when fixture goes out of scope
        request.addfinalizer(teardown)

        return host, mocked_method

    return on_call


@pytest.fixture
def host(request, tmpdir_factory):
    if not has_docker():
        pytest.skip('Skipping test because docker is not installed')
        return

    image, kw = parse_hostspec(request.param)
    host, user, _ = BaseBackend.parse_hostspec(image)
    user = user or 'root'
    hostspec = host

    scope = "session"
    if getattr(request.function, "destructive", None) is not None:
        scope = "function"

    fname = "_docker_container_%s_%s" % (host, scope)
    docker_id, docker_host, port = request.getfixturevalue(fname)
    hostname = docker_host

    if kw["connection"] == "docker":
        host = docker_id
        hostspec = user + '@' + host
        host = testinfra.host.get_host(hostspec, **kw)
        host.backend.get_hostname = lambda: image
        return host

    tmpdir = tmpdir_factory.mktemp(str(id(request)))
    key = tmpdir.join("ssh_key")
    key.write(open(os.path.join(BASETESTDIR, "ssh_key")).read())
    key.chmod(384)  # octal 600

    if kw["connection"] == "ansible":
        if ansible is None:
            pytest.skip('Skipping test because ansible is not installed')
            return

        setup_ansible_config(
            tmpdir, host, docker_host, user, port, str(key)
        )
        os.environ["ANSIBLE_CONFIG"] = str(tmpdir.join("ansible.cfg"))
        # this force backend cache reloading
        kw["ansible_inventory"] = str(tmpdir.join("inventory"))
        hostspec = host
    else:
        ssh_config = tmpdir.join("ssh_config")
        sut_ssh_config = build_generic_ssh_config(
            host=host,
            hostname=hostname,
            user=user,
            port=port,
            priv_key=key
        )
        ssh_config.write(sut_ssh_config)
        kw["ssh_config"] = str(ssh_config)
        hostspec = user + '@' + host

    # Wait ssh to be up
    service = testinfra.get_host(
        docker_id, connection='docker').service

    if image in ("centos_6", "centos_7", "fedora"):
        service_name = "sshd"
    else:
        service_name = "ssh"

    while not service(service_name).is_running:
        time.sleep(.5)

    host = testinfra.host.get_host(hostspec, **kw)
    host.backend.get_hostname = lambda: image
    return host


@pytest.fixture
def docker_image(host):
    return host.backend.get_hostname()


def pytest_generate_tests(metafunc):
    if 'vagrant_sut' in metafunc.fixturenames:
        marker = getattr(metafunc.function, 'vagrant_sut', None)
        params = (
            'vagrant://vagrant@default?vagrantfile=vagrant/macos-sierra/Vagrantfile',
        )
        if marker:
            params = (
                'vagrant://vagrant@default?' + '&'.join(
                    ['{}={}'.format(k, v) for k, v in marker.kwargs.items()]
                ),
            )
        metafunc.parametrize('vagrant_sut', params, indirect=True, scope='function')

    if "host" in metafunc.fixturenames:
        marker = getattr(metafunc.function, "testinfra_hosts", None)
        if marker is not None:
            hosts = marker.args
        else:
            # Default
            hosts = ["docker://debian_jessie"]

        metafunc.parametrize("host", hosts, indirect=True,
                             scope="function")


def pytest_configure(config):
    if not has_docker():
        return

    def build_image(build_failed, dockerfile, image, image_path):
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
