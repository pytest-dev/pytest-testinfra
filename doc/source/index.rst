.. include:: ../../README.rst

Invocation
==========


Test multiples hosts
~~~~~~~~~~~~~~~~~~~~

By default Testinfra launch tests on local machine, but you can also test
remotes systems::

    testinfra -v --hosts=localhost,root@webserver:2222 test_myinfra.py

    ====================== test session starts ======================
    platform linux -- Python 2.7.3 -- py-1.4.26 -- pytest-2.6.4
    plugins: testinfra
    collected 3 items 

    test_myinfra.py::test_passwd_file[localhost] PASSED
    test_myinfra.py::test_nginx_is_installed[localhost] PASSED
    test_myinfra.py::test_nginx_running_and_enabled[localhost] PASSED
    test_myinfra.py::test_passwd_file[root@webserver:2222] PASSED
    test_myinfra.py::test_nginx_is_installed[root@webserver:2222] PASSED
    test_myinfra.py::test_nginx_running_and_enabled[root@webserver:2222] PASSED

    =================== 6 passed in 8.49 seconds ====================


You can also set hosts per test module::

    hosts = ["localhost", "root@webserver:2222"]

    def test_foo(File, Package, Service):
        [...]


Testinfra use the command `ssh` for remote command execution, but it can
also use the paramiko_ module which use a persistent connection and thus
should be faster::

    pip install paramiko

    testinfra -v --hosts=localhost,root@webserver:2222 --connection=paramiko test_myinfra.py


If you have a lot a hosts to test, you can also use the pytest-xdist_ plugin to run tests using multiples process::


    pip install pytest-xdist

    testinfra -v --host=web1,web2,web3,web4,web5,web6 -n 3 test_myinfra.py


Advanced invocation
~~~~~~~~~~~~~~~~~~~

::

    # Test recursively all test files (starting with `test_`) in current directory
    testinfra

    # Filter function/hosts with pytest -k option
    testinfra -k webserver -k nginx


For more usages and features, see the Pytest_ documentation.


Nagios plugin
~~~~~~~~~~~~~

You can turn your test session into a nagios check::

    testinfra test_myinfra.py --nagios -qq

    TESTINFRA OK - 3 passed, 0 failed, 0 skipped in 0.14 seconds
    ...


Modules
=======

Testinfra modules are provided as `pytest fixtures`_, declare them as arguments
of your test function to make them available;

Command
~~~~~~~

.. class:: testinfra.modules.Command

    Run shell commands

    .. method:: __call__(command, *args)

    Run given command and return rc (exit status), stdout and stderr

    >>> cmd = Command("ls -l /etc/passwd")
    >>> cmd.rc
    0
    >>> cmd.stdout
    '-rw-r--r-- 1 root root 1790 Feb 11 00:28 /etc/passwd\n'
    >>> cmd.stderr
    ''

    Good practice: always use shell arguments quotting to avoid shell injection

    >>> cmd = Command("ls -l -- %s", "/;echo injection")
    CommandResult(
        rc=2, stdout='',
        stderr='ls: cannot access /;echo injection: No such file or directory\n',
        command="ls -l '/;echo injection'")

    .. method:: check_output(command, *args)

    Run given command, check if exit status is zero and return stdout without trailing newline character.

    Raises RuntimeError if exit status is non zero




File
~~~~

.. autoclass:: testinfra.modules.File
   :members:
   :undoc-members:


Group
~~~~~

.. autoclass:: testinfra.modules.Group
   :members:
   :undoc-members:


Interface
~~~~~~~~~

.. warning:: Support is currently limited to Linux systems

.. class:: testinfra.modules.Interface(name)

    .. attribute:: exists
    .. attribute:: speed
    .. attribute:: addresses

        Return ipv4 and ipv6 addresses on the interface

        >>> Interface("eth0").addresses
        ['192.168.31.254', '192.168.31.252', 'fe80::e291:f5ff:fe98:6b8c']


Package
~~~~~~~

.. class:: testinfra.modules.Package(name)

    .. attribute:: is_installed

    .. attribute:: version

    Return package version as returned by the package system

    >>> Package("nginx").version
    '1.2.1-2.2+wheezy3'

Service
~~~~~~~

.. class:: testinfra.modules.Service(name)

    Test services

    .. attribute:: is_running

    .. attribute:: is_enabled


SystemInfo
~~~~~~~~~~


.. autoclass:: testinfra.modules.SystemInfo
   :members:



.. toctree::
   :maxdepth: 2

.. _pytest fixtures: https://pytest.org/latest/fixture.html
