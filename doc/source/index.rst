.. include:: ../../README.rst

Invocation
==========


Test multiples hosts
~~~~~~~~~~~~~~~~~~~~

By default Testinfra launch tests on local machine, but you can also test
remotes systems using paramiko_ (a ssh implementation in python)::

    $ pip install paramiko
    $ testinfra -v --hosts=localhost,root@webserver:2222 test_myinfra.py

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


Parallel execution
~~~~~~~~~~~~~~~~~~

If you have a lot of tests, you can use the pytest-xdist_ plugin to run tests using multiples process::


    $ pip install pytest-xdist

    # Launch tests using 3 processes
    $ testinfra -n 3 -v --host=web1,web2,web3,web4,web5,web6 test_myinfra.py


Advanced invocation
~~~~~~~~~~~~~~~~~~~

::

    # Test recursively all test files (starting with `test_`) in current directory
    $ testinfra

    # Filter function/hosts with pytest -k option
    $ testinfra -k webserver -k nginx


For more usages and features, see the Pytest_ documentation.


Nagios plugin
~~~~~~~~~~~~~

You can turn your test session into a nagios check::

    $ testinfra test_myinfra.py --nagios -qq
    TESTINFRA OK - 3 passed, 0 failed, 0 skipped in 0.14 seconds
    ...


Connection backends
===================

Testinfra comes with several connections backends for remote command execution,
they are controlled with the ``--connection`` parameter.

local
~~~~~

This is the default backend when not hosts are provided (either via ``--hosts``
or in modules). Commands are run locally in a subprocess under the current
user. You can use the ``--sudo`` option to run commands as superuser::

    $ testinfra --sudo test_myinfra.py


paramiko
~~~~~~~~

This is the default backend when a hosts list is provided, paramiko_ is a
python implementation of SSHv2 protocol. Testinfra will not ask you for a
password, so you must be able to connect without password (using password less
keys or using ``ssh-agent``).

You can provide an alternate ssh-config and use sudo on the remote host::

    $ testinfra --ssh-config=/path/to/ssh_config --sudo --hosts=server

ssh
~~~

This is a pure ssh backend using the ``ssh`` command available in ``$PATH``. Example::

    $ testinfra --connection=ssh --hosts=server

The ssh backend also accept ``--ssh-config`` and ``--sudo`` parameters.


salt
~~~~

The salt backend use the `salt python client API
<http://docs.saltstack.com/en/latest/ref/clients/>`_ and can be used from the salt-master server::

    $ testinfra --connection=salt --hosts=minion1,minion2

Testinfra will use the salt connection channel to run commands.



Modules
=======

Testinfra modules are provided as `pytest fixtures`_, declare them as arguments
of your test function to make them available;

Command
~~~~~~~

.. autoclass:: testinfra.modules.Command(command, *args)
   :members: check_output, run_expect, run_test


File
~~~~

.. autoclass:: testinfra.modules.File
   :members:
   :undoc-members:
   :exclude-members: as_fixture


User
~~~~

.. autoclass:: testinfra.modules.User
   :members:
   :undoc-members:


Group
~~~~~

.. autoclass:: testinfra.modules.Group
   :members:
   :undoc-members:


Interface
~~~~~~~~~

.. autoclass:: testinfra.modules.Interface
   :members:
   :undoc-members:


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


Salt
~~~~


.. autoclass:: testinfra.modules.Salt(function, args=None)
   :members:


PuppetResource
~~~~~~~~~~~~~~


.. autoclass:: testinfra.modules.PuppetResource(type, name=None)
   :members:


Facter
~~~~~~


.. autoclass:: testinfra.modules.Facter(*facts)
   :members:


.. toctree::
   :maxdepth: 2

.. _pytest fixtures: https://pytest.org/latest/fixture.html
