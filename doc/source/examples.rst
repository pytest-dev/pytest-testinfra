Examples
========

Parametrize your tests
~~~~~~~~~~~~~~~~~~~~~~

Pytest support `test parametrization <https://pytest.org/latest/parametrize.html>`_::

    # BAD: If the test fails on nginx, python is not tested
    def test_packages(host):
        for name, version in (
            ("nginx", "1.6"),
            ("python", "2.7"),
        ):
            pkg = host.package(name)
            assert pkg.is_installed
            assert pkg.version.startswith(version)


    # GOOD: Each package is tested
    # $ py.test -v test.py
    # [...]
    # test.py::test_package[local-nginx-1.6] PASSED
    # test.py::test_package[local-python-2.7] PASSED
    # [...]
    import pytest

    @pytest.mark.parametrize("name,version", [
        ("nginx", "1.6"),
        ("python", "2.7"),
    ])
    def test_packages(host, name, version):
        pkg = host.package(name)
        assert pkg.is_installed
        assert pkg.version.startswith(version)


.. _make modules:


Using unittest
~~~~~~~~~~~~~~

Testinfra can be used with python standard unit test framework `unittest
<https://docs.python.org/3/library/unittest.html>`_ instead of pytest::

    import unittest
    import testinfra


    class Test(unittest.TestCase):

        def setUp(self):
            self.host = testinfra.get_host("paramiko://root@host")

        def test_nginx_config(self):
            self.assertEqual(self.host.run("nginx -t").rc, 0)

        def test_nginx_service(self):
            service = self.host.service("nginx")
            self.assertTrue(service.is_running)
            self.assertTrue(service.is_enabled)


    if __name__ == "__main__":
        unittest.main()


::

    $ python test.py
    ..
    ----------------------------------------------------------------------
    Ran 2 tests in 0.705s

    OK


Integration with vagrant
~~~~~~~~~~~~~~~~~~~~~~~~

`Vagrant <https://www.vagrantup.com/>`_ is a tool that setup and provision
development environment (virtual machines).

When your vagrant machine is up and running, you can easily run your testinfra
test suite on it::

    vagrant ssh-config > .vagrant/ssh-config
    testinfra --hosts=default --ssh-config=.vagrant/ssh-config tests.py


Integration with jenkins
~~~~~~~~~~~~~~~~~~~~~~~~

`Jenkins <https://jenkins-ci.org/>`_ is a well known open source continuous
integration server.

If your jenkins slave can run vagrant, your build scripts can be like::


    pip install testinfra paramiko
    vagrant up
    vagrant ssh-config > .vagrant/ssh-config
    py.test --hosts=default --ssh-config=.vagrant/ssh-config --junit-xml junit.xml tests.py


Then configure jenkins to get tests results from the `junit.xml` file.


Integration with nagios
~~~~~~~~~~~~~~~~~~~~~~~

The tests you will write with testinfra will usually be testing that the
services you're deploying run correctly. This kind of tests are close to
monitoring checks, so let's push them to `Nagios <https://www.nagios.org/>`_ !

Testinfra has an option `--nagios` that enable a compatible nagios plugin
beharvior::

    $ py.test -qq --nagios test_ok.py; echo $?
    TESTINFRA OK - 2 passed, 0 failed, 0 skipped in 2.30 seconds
    [...]
    0

    $ py.test -qq --nagios test_fail.py; echo $?
    TESTINFRA CRITICAL - 1 passed, 1 failed, 0 skipped in 2.24 seconds
    [Traceback that explain the failed test]
    2


You can run these tests from the nagios master or in the target host with
`NRPE <https://en.wikipedia.org/wiki/Nagios#Nagios_Remote_Plugin_Executor>`_.


Integration with KitchenCI
~~~~~~~~~~~~~~~~~~~~~~~~~~

KitchenCI (aka Test Kitchen) can use testinfra via its :code:`shell` verifier.
Add the following verifier to your :code:`.kitchen.yml`::

    verifier:
      name: shell
      command: py.test --host="paramiko://${KITCHEN_USERNAME}@${KITCHEN_HOSTNAME}:${KITCHEN_PORT}?ssh_identity_file=${KITCHEN_SSH_KEY}" --junit-xml "junit-${KITCHEN_INSTANCE}.xml" "test/integration/${KITCHEN_SUITE}"


.. _test docker images:

Test docker images
~~~~~~~~~~~~~~~~~~

Docker is a handy way to test your infrastructure code. This recipe show how to
build and run docker containers with testinfra by overwriting the `host`
fixture.

.. code-block:: python

    import pytest
    import subprocess
    import testinfra


    # By using scope = 'session' we use the same container for all tests, use
    # 'function' if you want a container per test function
    @pytest.fixture(scope='session')
    def host(request):
        # build local ./Dockerfile
        subprocess.check_call(['docker', 'build', '-t', 'myimage', '.'])
        # run a container
        docker_id = subprocess.check_output(
            ['docker', 'run', '-d', 'myimage']).decode().strip()
        # return a testinfra connection to the container
        yield testinfra.get_host("docker://" + docker_id)
        # at the end of the test suite, destroy the container
        subprocess.check_all(['docker', 'rm', '-f', docker_id])


    def test_myimage(host):
        # 'host' now bind to the container
        assert host.check_output('myapp -v') == 'Myapp 1.0'
