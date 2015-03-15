##################################
Testinfra test your infrastructure
##################################

About
=====

With Testinfra you can write unit tests in Python to test *actual state* of
yours servers configured by managements tools like Salt_, Ansible_, Puppet_,
Chef_ and so on.

Testinfra aims to be a ServerSpec_ equivalent in python and is written as
a plugin to the powerfull Pytest_ test engine

.. warning:: Testinfra is currently *alpha* software, API may change before the
             first release, and OS support is limited.


Quick start
===========

Install testinfra using pip::

    pip install testinfra

    # or install the devel version
    pip install 'git+https://github.com/philpep/testinfra@master#egg=testinfra'


Write your first tests to `test_myinfra.py`::

    from testinfra.modules import File, Package, Service

    def test_passwd_file():
        passwd = File("/etc/passwd")
        assert passwd.contains("root")
        assert passwd.user == "root"
        assert passwd.group == "root"
        assert passwd.mode == 644

    def test_nginx_is_installed():
        nginx = Package("nginx")
        assert nginx.is_installed
        assert nginx.version.startswith("1.2")

    def test_nginx_running_and_enabled():
        nginx = Service("nginx")
        assert nginx.is_running
        assert nginx.is_enabled


And run it::

    py.test -v test_myinfra.py


    ====================== test session starts ======================
    platform linux -- Python 2.7.3 -- py-1.4.26 -- pytest-2.6.4
    plugins: testinfra
    collected 3 items 

    test_myinfra.py::test_passwd_file[local] PASSED
    test_myinfra.py::test_nginx_is_installed[local] PASSED
    test_myinfra.py::test_nginx_running_and_enabled[local] PASSED

    =================== 3 passed in 0.66 seconds ====================


.. _Salt: http://saltstack.com/
.. _Ansible: http://www.ansible.com/
.. _Puppet: https://puppetlabs.com/
.. _Chef: https://www.chef.io/
.. _ServerSpec: http://serverspec.org/
.. _Pytest: http://pytest.org
.. _paramiko: http://www.paramiko.org/
.. _pytest-xdist: http://pytest.org/latest/xdist.html
