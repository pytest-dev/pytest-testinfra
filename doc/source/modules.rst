.. _modules:

Modules
=======

Testinfra modules are provided through the `host` `fixture`_, declare it as
arguments of your test function to make it available within it.

.. code-block:: python

    def test_foo(host):
        # [...]


host
~~~~

.. autoclass:: testinfra.host.Host
   :members:

    .. attribute:: ansible

       :class:`testinfra.modules.ansible.Ansible` class

    .. attribute:: addr

       :class:`testinfra.modules.addr.Addr` class

    .. attribute:: docker

       :class:`testinfra.modules.docker.Docker` class

    .. attribute:: environment

       :class:`testinfra.modules.environment.Environment` class

    .. attribute:: file

       :class:`testinfra.modules.file.File` class

    .. attribute:: group

       :class:`testinfra.modules.group.Group` class

    .. attribute:: interface

       :class:`testinfra.modules.interface.Interface` class

    .. attribute:: iptables

       :class:`testinfra.modules.iptables.Iptables` class

    .. attribute:: mount_point

       :class:`testinfra.modules.mountpoint.MountPoint` class

    .. attribute:: package

       :class:`testinfra.modules.package.Package` class

    .. attribute:: pip

       :class:`testinfra.modules.pip.Pip` class

    .. attribute:: pip_package

       :class:`testinfra.modules.pip.PipPackage` class

    .. attribute:: podman

       :class:`testinfra.modules.podman.Podman` class

    .. attribute:: process

       :class:`testinfra.modules.process.Process` class

    .. attribute:: puppet_resource

       :class:`testinfra.modules.puppet.PuppetResource` class

    .. attribute:: facter

       :class:`testinfra.modules.puppet.Facter` class

    .. attribute:: salt

       :class:`testinfra.modules.salt.Salt` class

    .. attribute:: service

       :class:`testinfra.modules.service.Service` class

    .. attribute:: socket

       :class:`testinfra.modules.socket.Socket` class

    .. attribute:: sudo

       :class:`testinfra.modules.sudo.Sudo` class

    .. attribute:: supervisor

       :class:`testinfra.modules.supervisor.Supervisor` class

    .. attribute:: sysctl

       :class:`testinfra.modules.sysctl.Sysctl` class

    .. attribute:: system_info

       :class:`testinfra.modules.systeminfo.SystemInfo` class

    .. attribute:: user

       :class:`testinfra.modules.user.User` class




Ansible
~~~~~~~

.. autoclass:: testinfra.modules.ansible.Ansible(module_name, module_args=None, check=True)
   :members:


Addr
~~~~

.. autoclass:: testinfra.modules.addr.Addr(name)
   :members:


Docker
~~~~~~

.. autoclass:: testinfra.modules.docker.Docker(name)
   :members:


File
~~~~

.. autoclass:: testinfra.modules.file.File
   :members:
   :undoc-members:
   :exclude-members: get_module_class


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


Iptables
~~~~~~~~~

.. autoclass:: testinfra.modules.iptables.Iptables
   :members:
   :undoc-members:


MountPoint
~~~~~~~~~~

.. autoclass:: testinfra.modules.mountpoint.MountPoint(path)
   :members:


Package
~~~~~~~

.. autoclass:: testinfra.modules.package.Package
   :members:


Pip
~~~~~~~~~~

.. autoclass:: testinfra.modules.pip.Pip
   :members:


PipPackage
~~~~~~~~~~

.. autoclass:: testinfra.modules.pip.PipPackage


Podman
~~~~~~

.. autoclass:: testinfra.modules.podman.Podman(name)
   :members:


Process
~~~~~~~

.. autoclass:: testinfra.modules.process.Process
   :members:


PuppetResource
~~~~~~~~~~~~~~

.. autoclass:: testinfra.modules.puppet.PuppetResource(type, name=None)
   :members:


Facter
~~~~~~

.. autoclass:: testinfra.modules.puppet.Facter(*facts)
   :members:


Salt
~~~~

.. autoclass:: testinfra.modules.salt.Salt(function, args=None, local=False, config=None)
   :members:


Service
~~~~~~~

.. autoclass:: testinfra.modules.service.Service
   :members:


Socket
~~~~~~

.. autoclass:: testinfra.modules.socket.Socket
   :members:


Sudo
~~~~

.. autoclass:: testinfra.modules.sudo.Sudo(user=None)


Supervisor
~~~~~~~~~~

.. autoclass:: testinfra.modules.supervisor.Supervisor
   :members:


Sysctl
~~~~~~

.. autoclass:: testinfra.modules.sysctl.Sysctl(name)
   :members:


SystemInfo
~~~~~~~~~~

.. autoclass:: testinfra.modules.systeminfo.SystemInfo
   :members:


User
~~~~

.. autoclass:: testinfra.modules.user.User
   :members:
   :exclude-members: get_module_class


.. _fixture: https://docs.pytest.org/en/latest/fixture.html#fixture
