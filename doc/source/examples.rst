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

Testinfra can be used with the standard Python unit test framework `unittest
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


Integration with Vagrant
~~~~~~~~~~~~~~~~~~~~~~~~

`Vagrant <https://www.vagrantup.com/>`_ is a tool to setup and provision
development environments (virtual machines).

When your Vagrant machine is up and running, you can easily run your testinfra
test suite on it::

    vagrant ssh-config > .vagrant/ssh-config
    py.test --hosts=default --ssh-config=.vagrant/ssh-config tests.py


Integration with Jenkins
~~~~~~~~~~~~~~~~~~~~~~~~

`Jenkins <https://jenkins-ci.org/>`_ is a well known open source continuous
integration server.

If your Jenkins slave can run Vagrant, your build scripts can be like::


    pip install pytest-testinfra paramiko
    vagrant up
    vagrant ssh-config > .vagrant/ssh-config
    py.test --hosts=default --ssh-config=.vagrant/ssh-config --junit-xml junit.xml tests.py


Then configure Jenkins to get tests results from the `junit.xml` file.


Integration with Nagios
~~~~~~~~~~~~~~~~~~~~~~~

Your tests will usually be validating that the services you are deploying run correctly.
This kind of tests are close to monitoring checks, so let's push them to
`Nagios <https://www.nagios.org/>`_ !

The Testinfra option `--nagios` enables a behavior compatible with a nagios plugin::


    $ py.test -qq --nagios --tb line test_ok.py; echo $?
    TESTINFRA OK - 2 passed, 0 failed, 0 skipped in 2.30 seconds
    ..
    0

    $ py.test -qq --nagios --tb line test_fail.py; echo $?
    TESTINFRA CRITICAL - 1 passed, 1 failed, 0 skipped in 2.24 seconds
    .F
    /usr/lib/python3/dist-packages/example/example.py:95: error: [Errno 111] error msg
    2


You can run these tests from the nagios master or in the target host with
`NRPE <https://en.wikipedia.org/wiki/Nagios#Nagios_Remote_Plugin_Executor>`_.


Integration with KitchenCI
~~~~~~~~~~~~~~~~~~~~~~~~~~

KitchenCI (aka Test Kitchen) can use testinfra via its :code:`shell` verifier.
Add the following to your :code:`.kitchen.yml`, this requires installing `paramiko` 
additionaly (on your host machine, not in the VM handled by kitchen) ::

    verifier:
      name: shell
      command: py.test --hosts="paramiko://${KITCHEN_USERNAME}@${KITCHEN_HOSTNAME}:${KITCHEN_PORT}?ssh_identity_file=${KITCHEN_SSH_KEY}" --junit-xml "junit-${KITCHEN_INSTANCE}.xml" "test/integration/${KITCHEN_SUITE}"


.. _test docker images:

Test Docker images
~~~~~~~~~~~~~~~~~~

Docker is a handy way to test your infrastructure code. This recipe shows how to
build and run Docker containers with Testinfra by overloading the `host`
fixture.

.. code-block:: python

    import pytest
    import subprocess
    import testinfra


    # scope='session' uses the same container for all the tests;
    # scope='function' uses a new container per test function.
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
        subprocess.check_call(['docker', 'rm', '-f', docker_id])


    def test_myimage(host):
        # 'host' now binds to the container
        assert host.check_output('myapp -v') == 'Myapp 1.0'
