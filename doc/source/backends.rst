Connection backends
===================

Testinfra comes with several connections backends for remote command execution,
they are controlled with the ``--connection`` parameter.

For all backends, command can be run as superuser with the ``--sudo``
option or as specific user by adding a ``--sudo-user`` option.

local
~~~~~

This is the default backend when not hosts are provided (either via
``--hosts`` or in modules). Commands are run locally in a subprocess under
the current user::

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

    $ testinfra --connection=salt # equivalent to --hosts='*'
    $ testinfra --connection=salt --hosts=minion1,minion2
    $ testinfra --connection=salt --hosts='web*'
    $ testinfra --connection=salt --hosts=G@os:Debian

Testinfra will use the salt connection channel to run commands.

Host can be seleted using `glob` or `compound matchers
<https://docs.saltstack.com/en/latest/topics/targeting/compound.html>`_.


.. _ansible connection backend:

ansible
~~~~~~~


The ansible backend use the `ansible python API
<https://docs.ansible.com/ansible/developing_api.html>`_::

    $ testinfra --connection=ansible # tests all inventory hosts
    $ testinfra --connection=ansible --hosts=host1,host2
    $ testinfra --connection=ansible --hosts='web*'

You can use an alternative `inventory` with the ``--ansible-inventory`` option.

Note: Ansible settings such as ``remote_user``, etc., may be configured by using Ansible's
`environment variables <http://docs.ansible.com/ansible/intro_configuration.html#environmental-configuration>`_.


kubectl
~~~~~~~

The kubectl backend can be used to test containers running in Kubernetes.
It use the `kubectl exec <http://kubernetes.io/docs/user-guide/kubectl/kubectl_exec/>`_ command::

    $ testinfra --connection=kubectl --hosts=pod_id-123456789-9fng/container_name
