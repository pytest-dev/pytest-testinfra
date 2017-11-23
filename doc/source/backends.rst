Connection backends
===================

Testinfra comes with several connections backends for remote command execution,
they are selected with the ``--connection`` option.

For all backends, commands can be run as superuser with the ``--sudo``
option or as specific user with the ``--sudo-user`` option.

local
~~~~~

This is the default backend when no hosts are provided (either via
``--hosts`` or in modules). Commands are run locally in a subprocess under
the current user::

    $ py.test --sudo test_myinfra.py


paramiko
~~~~~~~~

This is the default backend when a hosts list is provided. `Paramiko
<http://www.paramiko.org>`_ is a Python implementation of the SSHv2
protocol. Testinfra will not ask you for a password, so you must be
able to connect without password (using passwordless keys or using
``ssh-agent``).

You can provide an alternate ssh-config::

    $ py.test --ssh-config=/path/to/ssh_config --hosts=server


docker
~~~~~~

The Docker backend can be used to test *running* containers. It uses the `docker
exec <https://docs.docker.com/reference/commandline/exec/>`_ command::

    $ py.test --connection=docker --hosts=[user@]docker_id_or_name

See also the :ref:`Test docker images` example.


ssh
~~~

This is a pure SSH backend using the ``ssh`` command available in ``$PATH``. Example::

    $ py.test --connection=ssh --hosts=server

The ssh backend also accepts the ``--ssh-config`` option.


salt
~~~~

The salt backend uses the `salt Python client API
<http://docs.saltstack.com/en/latest/ref/clients/>`_ and can be used from the salt-master server::

    $ py.test --connection=salt # equivalent to --hosts='*'
    $ py.test --connection=salt --hosts=minion1,minion2
    $ py.test --connection=salt --hosts='web*'
    $ py.test --connection=salt --hosts=G@os:Debian

Testinfra will use the salt connection channel to run commands.

Hosts can be seleted by using the `glob` and `compound matchers
<https://docs.saltstack.com/en/latest/topics/targeting/compound.html>`_.


.. _ansible connection backend:

ansible
~~~~~~~


The ansible backend uses the `ansible Python API
<https://docs.ansible.com/ansible/developing_api.html>`_::

    $ py.test --connection=ansible # tests all inventory hosts
    $ py.test --connection=ansible --hosts=host1,host2
    $ py.test --connection=ansible --hosts='web*'

You can use an alternative `inventory` with the ``--ansible-inventory`` option.

Note: Ansible settings such as ``remote_user``, etc., may be configured by using Ansible's
`environment variables <http://docs.ansible.com/ansible/intro_configuration.html#environmental-configuration>`_.


kubectl
~~~~~~~

The kubectl backend can be used to test containers running in Kubernetes.
It uses the `kubectl exec <http://kubernetes.io/docs/user-guide/kubectl/kubectl_exec/>`_ command::

    $ py.test --connection=kubectl --hosts=pod_id-123456789-9fng/container_name


winrm
~~~~~

The winrm backend uses `pywinrm <https://pypi.python.org/pypi/pywinrm>`_::

    $ py.test --hosts='winrm://Administrator:Password@127.0.0.1'
    $ py.test --connection=winrm --hosts='vagrant@127.0.0.1:2200?no_ssl=true&no_verify_ssl=true'
