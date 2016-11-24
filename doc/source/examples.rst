Examples
========

Parametrize your tests
~~~~~~~~~~~~~~~~~~~~~~

Pytest support `test parametrization <https://pytest.org/latest/parametrize.html>`_::

    # BAD: If the test fails on nginx, python is not tested
    def test_packages(Package):
        for name, version in (
            ("nginx", "1.6"),
            ("python", "2.7"),
        ):
            assert Package(name).is_installed
            assert Package(name).version.startswith(version)


    # GOOD: Each package is tested
    # $ testinfra -v test.py
    # [...]
    # test.py::test_package[local-nginx-1.6] PASSED
    # test.py::test_package[local-python-2.7] PASSED
    # [...]
    import pytest

    @pytest.mark.parametrize("name,version", [
        ("nginx", "1.6"),
        ("python", "2.7"),
    ])
    def test_packages(Package, name, version):
        assert Package(name).is_installed
        assert Package(name).version.startswith(version)


.. _make modules:


Using unittest
~~~~~~~~~~~~~~

Testinfra can be used with python standard unit test framework `unittest
<https://docs.python.org/3/library/unittest.html>`_ instead of pytest::

    import unittest
    import testinfra


    class Test(unittest.TestCase):

        def setUp(self):
            self.b = testinfra.get_backend("paramiko://root@host")

        def test_nginx_config(self):
            self.assertEqual(self.b.Command("nginx -t").rc, 0)

        def test_nginx_service(self):
            service = self.b.Service("nginx")
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


Make your own modules
~~~~~~~~~~~~~~~~~~~~~

Suppose you want to create a simple wrapper around the `echo` command. You just
have to declare a `pytest fixture <https://pytest.org/latest/fixture.html>`_::

    import pytest

    @pytest.fixture()
    def Echo(Command):
        def f(arg):
            return Command.check_output("echo %s", arg)
        return f


    def test(Echo):
        assert Echo("foo") == "foo"


If you want to use it in all your test file, just put it in a `conftest.py
<https://pytest.org/latest/plugins.html>`_ file.


Share your modules
~~~~~~~~~~~~~~~~~~

Suppose you wrote a more useful module than the echo wrapper above and want to
share with the entire world. You can package your plugin as a `pytest plugin
<https://pytest.org/latest/plugins.html>`_.

See `philpep/testinfra-echo <https://github.com/philpep/testinfra-echo>`_ to
see an example of pytest plugin based on testinfra.


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
    testinfra --hosts=default --ssh-config=.vagrant/ssh-config --junit-xml junit.xml tests.py


Then configure jenkins to get tests results from the `junit.xml` file.

If you use the `docker provisioner
<https://docs.vagrantup.com/v2/provisioning/docker.html>`_ in vagrant, and use
the `docker plugin
<https://wiki.jenkins-ci.org/display/JENKINS/Docker+Plugin>`_ in jenkins, you
might be interested by the `philpep/jenkins-slave:jessie
<https://github.com/philpep/jenkins-slave>`_ docker image. This is the image
used to tests testinfra itself using vagrant and docker (in docker).


Integration with nagios
~~~~~~~~~~~~~~~~~~~~~~~

The tests you will write with testinfra will usually be testing that the
services you're deploying run correctly. This kind of tests are close to
monitoring checks, so let's push them to `Nagios <https://www.nagios.org/>`_ !

Testinfra has an option `--nagios` that enable a compatible nagios plugin
beharvior::

    $ testinfra -qq --nagios test_ok.py; echo $?
    TESTINFRA OK - 2 passed, 0 failed, 0 skipped in 2.30 seconds
    [...]
    0

    $ testinfra -qq --nagios test_fail.py; echo $?
    TESTINFRA CRITICAL - 1 passed, 1 failed, 0 skipped in 2.24 seconds
    [Traceback that explain the failed test]
    2


You can run these tests from the nagios master or in the target host with
`NRPE <https://en.wikipedia.org/wiki/Nagios#Nagios_Remote_Plugin_Executor>`_.


.. _test docker images:

Test docker images
~~~~~~~~~~~~~~~~~~

Docker is a handy way to test your infrastructure code. This recipe show
how to test the resulting docker image with testinfra and provides awesome
features like testing multiple images and run some destructive tests on a
dedicated container.

This will use advanced pytest features, to understand the underlying
concepts read the pytest documentation:

    - https://pytest.org/latest/fixture.html
    - https://pytest.org/latest/parametrize.html
    - https://pytest.org/latest/example/markers.html



Put this code in a `conftest.py` file:

.. code-block:: python

    import pytest
    import testinfra

    # Use testinfra to get a handy function to run commands locally
    check_output = testinfra.get_backend(
        "local://"
    ).get_module("Command").check_output


    @pytest.fixture
    def TestinfraBackend(request):
        # Override the TestinfraBackend fixture,
        # all testinfra fixtures (i.e. modules) depend on it.

        docker_id = check_output(
            "docker run -d %s tail -f /dev/null", request.param)

        def teardown():
            check_output("docker rm -f %s", docker_id)

        # Destroy the container at the end of the fixture life
        request.addfinalizer(teardown)

        # Return a dynamic created backend
        return testinfra.get_backend("docker://" + docker_id)


    def pytest_generate_tests(metafunc):
        if "TestinfraBackend" in metafunc.fixturenames:

            # Lookup "docker_images" marker
            marker = getattr(metafunc.function, "docker_images", None)
            if marker is not None:
                images = marker.args
            else:
                # Default image
                images = ["debian:jessie"]

            # If the test has a destructive marker, we scope TestinfraBackend
            # at function level (i.e. executing for each test). If not we scope
            # at session level (i.e. all tests will share the same container)
            if getattr(metafunc.function, "destructive", None) is not None:
                scope = "function"
            else:
                scope = "session"

            metafunc.parametrize(
                "TestinfraBackend", images, indirect=True, scope=scope)



Then create a `test_docker.py` file with our testinfra tests:

.. code-block:: python

    import pytest

    # To mark all the tests as destructive:
    # pytestmark = pytest.mark.destructive

    # To run all the tests on given docker images:
    # pytestmark = pytest.mark.docker_images("debian:jessie", "centos:7")

    # Both
    # pytestmark = [
    #     pytest.mark.destructive,
    #     pytest.mark.docker_images("debian:jessie", "centos:7")
    # ]


    # This test will run on default image (debian:jessie)
    def test_default(Process):
        assert Process.get(pid=1).comm == "tail"


    # This test will run on both debian:jessie and centos:7 images
    @pytest.mark.docker_images("debian:jessie", "centos:7")
    def test_multiple(Process):
        assert Process.get(pid=1).comm == "tail"


    # This test is marked as destructive and will run on its own container
    # It will create a /foo file and run 3 times with different params
    @pytest.mark.destructive
    @pytest.mark.parametrize("content", ["bar", "baz", "qux"])
    def test_destructive(Command, File, content):
        assert not File("/foo").exists
        Command.check_output("echo %s > /foo", content)
        assert File("/foo").content == content + "\n"


Now let's run it::

    $ testinfra -v
    [...]

    test_docker.py::test_default[debian:jessie] PASSED
    test_docker.py::test_multiple[debian:jessie] PASSED
    test_docker.py::test_multiple[centos:7] PASSED
    test_docker.py::test_destructive[debian:jessie-bar] PASSED
    test_docker.py::test_destructive[debian:jessie-baz] PASSED
    test_docker.py::test_destructive[debian:jessie-qux] PASSED


Note that you can speedup the tests execution by using pytest-xdist.
