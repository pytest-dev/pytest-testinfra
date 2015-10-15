.. _modules:

Modules
=======

Testinfra modules are provided as `pytest fixtures`_, declare them as
arguments of your test function to make them available::

    def test_foo(Package, File, Command):
        [...]


Note that you can also :ref:`make modules`.

Command
~~~~~~~

.. autoclass:: testinfra.modules.Command(command, *args)
   :members: check_output, run_expect, run_test


LocalCommand
~~~~~~~~~~~~

Same as `Command` but run commands locally with subprocess even when the
connection backend is not "local".


File
~~~~

.. autoclass:: testinfra.modules.File(path)
   :members:
   :undoc-members:
   :exclude-members: as_fixture, get_module


User
~~~~

.. autoclass:: testinfra.modules.User(name=None)
   :members:
   :undoc-members:


Group
~~~~~

.. autoclass:: testinfra.modules.Group(name)
   :members:
   :undoc-members:


Interface
~~~~~~~~~

.. autoclass:: testinfra.modules.Interface(name)
   :members:
   :undoc-members:
   :exclude-members: get_module


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


.. autoclass:: testinfra.modules.SystemInfo()
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

Sysctl
~~~~~~

.. autoclass:: testinfra.modules.Sysctl(name)
   :members:


Port
~~~~

.. autoclass:: testinfra.modules.Port(address, port)
   :members:
   :undoc-members:
   :exclude-members: get_module

.. _pytest fixtures: https://pytest.org/latest/fixture.html
