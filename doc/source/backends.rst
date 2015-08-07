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

This is the default backend when a hosts list is provided, `paramiko
<http://www.paramiko.org>`_ is a python implementation of SSHv2
protocol. Testinfra will not ask you for a password, so you must be
able to connect without password (using password less keys or using
``ssh-agent``).

You can provide an alternate ssh-config and use sudo on the remote host::

    $ testinfra --ssh-config=/path/to/ssh_config --sudo --hosts=server


docker
~~~~~~

The docker backend can be used to test *running* containers. It use the `docker
exec <https://docs.docker.com/reference/commandline/exec/>`_ command::

    $ testinfra --connection=docker --hosts=[user@]docker_id_or_name

See also the :ref:`Test docker images` example.

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
