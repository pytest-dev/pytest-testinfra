Examples
========

Parametrize test
~~~~~~~~~~~~~~~~

This examples introduces some usefull `pytest <http://pytest.org>`_ features.
Especially about proper and efficient looping in tests assertions.

The purpose of the test is to verify the security of php config by
checking the `disable_functions
<http://php.net/manual/fr/ini.core.php#ini.disable-functions>`_
parameter.

Let's write our first attempt in `test_php.py`

.. literalinclude:: test_php.py

Now run it and see what if a test fail::

    $ testinfra -v --hosts=root@webserver test_php.py
    [...]

    test_php.py::test_php_disable_functions[root@webserver] FAILED

    [...]

    >           assert func in disabled_functions
    E           assert 'popen' in set(['eval', 'exec', 'parse_ini_file', 'passthru', 'pcntl_alarm', 'pcntl_exec', ...])

    test_php.py:24: AssertionError

    ==== 1 failed in 0.39 seconds ====



Here ``popen`` is missing, but **the test stops after the first failed
assertion**, so we don't have any information about the functions after
``popen`` in the list.

Let's improve the code by using `pytest parametrize feature <https://pytest.org/latest/parametrize.html>`_:

.. literalinclude:: test_php2.py


Run it::

    $ testinfra -v --hosts=root@webserver test_php.py
    [...]
    test_php.py::test_php_disable_functions[root@webserver-show_source] PASSED
    test_php.py::test_php_disable_functions[root@webserver-shell_exec] PASSED
    test_php.py::test_php_disable_functions[root@webserver-popen] FAILED
    test_php.py::test_php_disable_functions[root@webserver-proc_open] FAILED
    test_php.py::test_php_disable_functions[root@webserver-passthru] PASSED
    test_php.py::test_php_disable_functions[root@webserver-exec] PASSED
    test_php.py::test_php_disable_functions[root@webserver-eval] PASSED
    [...]
    test_php.py::test_php_disable_functions[root@webserver-pcntl_getpriority] PASSED
    test_php.py::test_php_disable_functions[root@webserver-pcntl_setpriority] PASSED
    test_php.py::test_php_disable_functions[root@webserver-curl_exec] FAILED
    test_php.py::test_php_disable_functions[root@webserver-curl_milti_exec] FAILED

    ==== 4 failed, 28 passed in 17.07 seconds ====


Now we have a detailed output because each function is a test case. But wait,
this test takes 17 seconds because it launch a ``grep`` command for each
function (32 functions)...

Let's optimize this by using a `pytest fixture
<https://pytest.org/latest/fixture.html>`_. A fixture is a kind of shared code
or resource for our tests. A module scoped fixture will run once per module and
per host.

.. literalinclude:: test_php3.py


Run it::

    $ testinfra -v --hosts=root@webserver test_php.py
    [...]
    test_php.py::test_php_disable_functions[root@webserver-show_source] PASSED
    test_php.py::test_php_disable_functions[root@webserver-shell_exec] PASSED
    test_php.py::test_php_disable_functions[root@webserver-popen] FAILED
    test_php.py::test_php_disable_functions[root@webserver-proc_open] FAILED
    test_php.py::test_php_disable_functions[root@webserver-passthru] PASSED
    test_php.py::test_php_disable_functions[root@webserver-exec] PASSED
    test_php.py::test_php_disable_functions[root@webserver-eval] PASSED
    [...]
    test_php.py::test_php_disable_functions[root@webserver-pcntl_exec] PASSED
    test_php.py::test_php_disable_functions[root@webserver-pcntl_getpriority] PASSED
    test_php.py::test_php_disable_functions[root@webserver-pcntl_setpriority] PASSED
    test_php.py::test_php_disable_functions[root@webserver-curl_exec] FAILED
    test_php.py::test_php_disable_functions[root@webserver-curl_milti_exec] FAILED

    ==== 4 failed, 28 passed in 0.42 seconds ====

Ok less than one second.
