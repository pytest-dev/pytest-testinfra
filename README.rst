##################################
Testinfra test your infrastructure
##################################

Latest documentation: https://testinfra.readthedocs.io/en/latest

About
=====

With Testinfra you can write unit tests in Python to test *actual state* of
your servers configured by management tools like Salt_, Ansible_, Puppet_,
Chef_ and so on.

Testinfra aims to be a Serverspec_ equivalent in python and is written as
a plugin to the powerful Pytest_ test engine

License
=======

`Apache License 2.0 <https://github.com/pytest-dev/pytest-testinfra/blob/master/LICENSE>`_

The logo is licensed under the `Creative Commons NoDerivatives 4.0 License <https://creativecommons.org/licenses/by-nd/4.0/>`_
If you have some other use in mind, contact us.

Quick start
===========

Install testinfra using pip::

    $ pip install pytest-testinfra

    # or install the devel version
    $ pip install 'git+https://github.com/pytest-dev/pytest-testinfra@master#egg=pytest-testinfra'


Write your first tests file to `test_myinfra.py`:

.. code-block:: python

    def test_passwd_file(host):
        passwd = host.file("/etc/passwd")
        assert passwd.contains("root")
        assert passwd.user == "root"
        assert passwd.group == "root"
        assert passwd.mode == 0o644


    def test_nginx_is_installed(host):
        nginx = host.package("nginx")
        assert nginx.is_installed
        assert nginx.version.startswith("1.2")


    def test_nginx_running_and_enabled(host):
        nginx = host.service("nginx")
        assert nginx.is_running
        assert nginx.is_enabled


And run it::

    $ py.test -v test_myinfra.py


    ====================== test session starts ======================
    platform linux -- Python 2.7.3 -- py-1.4.26 -- pytest-2.6.4
    plugins: testinfra
    collected 3 items

    test_myinfra.py::test_passwd_file[local] PASSED
    test_myinfra.py::test_nginx_is_installed[local] PASSED
    test_myinfra.py::test_nginx_running_and_enabled[local] PASSED

    =================== 3 passed in 0.66 seconds ====================


.. _Salt: https://saltstack.com/
.. _Ansible: https://www.ansible.com/
.. _Puppet: https://puppetlabs.com/
.. _Chef: https://www.chef.io/
.. _Serverspec: https://serverspec.org/
.. _Pytest: https://pytest.org/
