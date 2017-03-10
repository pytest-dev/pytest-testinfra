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

.. autoclass:: testinfra.modules.command.Command(command, *args)
   :members: check_output, run_expect, run_test, exists


LocalCommand
~~~~~~~~~~~~


.. autofunction:: testinfra.plugin.LocalCommand(command, *args)


TestinfraBackend
~~~~~~~~~~~~~~~~

.. autoclass:: testinfra.backend.base.BaseBackend()
   :members:


Sudo
~~~~

.. autoclass:: testinfra.modules.sudo.Sudo(user=None)


File
~~~~

.. autoclass:: testinfra.modules.file.File
   :members:
   :undoc-members:
   :exclude-members: get_module_class


User
~~~~

.. autoclass:: testinfra.modules.user.User
   :members:
   :undoc-members:


Group
~~~~~

.. autoclass:: testinfra.modules.group.Group
   :members:
   :undoc-members:


Interface
~~~~~~~~~

.. autoclass:: testinfra.modules.interface.Interface
   :members:
   :undoc-members:
   :exclude-members: get_module_class


Package
~~~~~~~

.. autoclass:: testinfra.modules.package.Package
   :members:


PipPackage
~~~~~~~~~~

.. autoclass:: testinfra.modules.pip.PipPackage
   :members:

Process
~~~~~~~

.. autoclass:: testinfra.modules.process.Process
   :members:

Service
~~~~~~~

.. autoclass:: testinfra.modules.service.Service
   :members:


Supervisor
~~~~~~~~~~

.. autoclass:: testinfra.modules.supervisor.Supervisor
   :members:


Socket
~~~~~~

.. autoclass:: testinfra.modules.socket.Socket
   :members:


SystemInfo
~~~~~~~~~~


.. autoclass:: testinfra.modules.systeminfo.SystemInfo
   :members:


Salt
~~~~


.. autoclass:: testinfra.modules.salt.Salt(function, args=None)
   :members:

Ansible
~~~~~~~

.. autoclass:: testinfra.modules.ansible.Ansible(module_name, module_args=None, check=True)
   :members:


PuppetResource
~~~~~~~~~~~~~~


.. autoclass:: testinfra.modules.puppet.PuppetResource(type, name=None)
   :members:


Facter
~~~~~~


.. autoclass:: testinfra.modules.puppet.Facter(*facts)
   :members:

Sysctl
~~~~~~

.. autoclass:: testinfra.modules.sysctl.Sysctl(name)
   :members:


MountPoint
~~~~~~~~~~

.. autoclass:: testinfra.modules.mountpoint.MountPoint(path)
   :members:

.. _pytest fixtures: https://pytest.org/latest/fixture.html
