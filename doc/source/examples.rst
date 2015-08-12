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
