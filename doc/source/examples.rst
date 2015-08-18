Examples
========

.. _make modules:

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

This recipe shows how to run and destroy a docker container for each test
function::

    import pytest

    testinfra_hosts = ["docker://test_jessie"]


    @pytest.fixture(autouse=True, scope="function")
    def _docker_marker(request, LocalCommand):
        # Each test decorated with @pytest.mark.docker will run a docker container
        # named test_jessie
        marker = request.keywords.get('docker', None)
        if marker:
            LocalCommand.check_output("docker run -d --name test_jessie debian:jessie tail -f /dev/null")

            def teardown():
                LocalCommand.check_output("docker kill test_jessie")
                LocalCommand.check_output("docker rm test_jessie")

            # At the end of each test, we destroy the previously created container.
            request.addfinalizer(teardown)


    @pytest.mark.docker
    def test_command(Command, File):
        Command.check_output("echo foo > /foo")
        assert File("/foo").content == "foo\n"


    @pytest.mark.docker
    def test_command2(File):
        # As you can see, the container is recreated for each test function
        assert not File("/foo").exists


If you want to use the same container for all tests in a module or in a
session, you just have to change the scope of the `_docker_marker` fixture to
`module` or `session`.
