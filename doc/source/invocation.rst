Invocation
==========


Test multiples hosts
~~~~~~~~~~~~~~~~~~~~

By default Testinfra launch tests on local machine, but you can also
test remotes systems using `paramiko <https://www.paramiko.org>`_ (a
ssh implementation in python)::

    $ pip install paramiko
    $ py.test -v --hosts=localhost,root@webserver:2222 test_myinfra.py

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

    testinfra_hosts = ["localhost", "root@webserver:2222"]

    def test_foo(host):
        [....]



Parallel execution
~~~~~~~~~~~~~~~~~~

If you have a lot of tests, you can use the pytest-xdist_ plugin to run tests using multiples process::


    $ pip install pytest-xdist

    # Launch tests using 3 processes
    $ py.test -n 3 -v --host=web1,web2,web3,web4,web5,web6 test_myinfra.py


Advanced invocation
~~~~~~~~~~~~~~~~~~~

::

    # Test recursively all test files (starting with `test_`) in current directory
    $ py.test

    # Filter function/hosts with pytest -k option
    $ py.test --hosts=webserver,dnsserver -k webserver -k nginx


For more usages and features, see the Pytest_ documentation.


.. _Pytest: https://docs.pytest.org/en/latest/
.. _pytest-xdist: https://pypi.org/project/pytest-xdist/

Delegation
~~~~~~~~~~

If testinfra is used with Ansible backend, it is possible to create
another Host object using `delegate_to` fixture. This fixture is a function
which can produce a new Host object based on `host_specs` parameter
(e.g. "ansible://foo" or "ansible://bar?force_ansible").

It can delegate only to one host (no parametrization), so fixture fail
if there are more than one host resolved from host_specs to host list.

If host_specs resolves to empty list, fixture either fail test
or skip it, depending on value of optional parameter `skip_empty`
(default value is False, meaning 'fail the test if hostlist is empty').

With `skip_empty=True` (i.e. `delegate_to("ansible://foo", skip_empty=True)`,
if there are no hosts for a given host_specs, test is skipped.

See :ref:`Using delegation` for examples.
