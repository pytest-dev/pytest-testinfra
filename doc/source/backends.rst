Connection backends
===================

Testinfra comes with several connections backends for remote command execution.

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

    $ py.test --hosts='docker://[user@]docker_id_or_name'

See also the :ref:`Test docker images` example.


ssh
~~~

This is a pure SSH backend using the ``ssh`` command available in ``$PATH``. Example::

    $ py.test --hosts='ssh://server'

The ssh backend also accepts the ``--ssh-config`` option.


salt
~~~~

The salt backend uses the `salt Python client API
<http://docs.saltstack.com/en/latest/ref/clients/>`_ and can be used from the salt-master server::

    $ py.test --hosts='salt://*'
    $ py.test --hosts='salt://minion1,salt://minion2'
    $ py.test --hosts='salt://web*'
    $ py.test --hosts='salt://G@os:Debian'

Testinfra will use the salt connection channel to run commands.

Hosts can be seleted by using the `glob` and `compound matchers
<https://docs.saltstack.com/en/latest/topics/targeting/compound.html>`_.


.. _ansible connection backend:

ansible
~~~~~~~

The ansible backend is able to parse ansible inventories to get host connection
details, including ``ansible_become`` and ``ansible_become_user``. It only
works with local, ssh or docker hosts::

    $ py.test --hosts=all # tests all inventory hosts
    $ py.test --hosts='ansible://host1,ansible://host2'
    $ py.test --hosts='ansible://web*'

kubectl
~~~~~~~

The kubectl backend can be used to test containers running in Kubernetes.  It
uses the `kubectl exec <http://kubernetes.io/docs/user-guide/kubectl/kubectl_exec/>`_ command and
support connecting to a given container name within a pod and using a given
namespace::

    # will use the default namespace and default container
    $ py.test --hosts='kubectl://mypod-a1b2c3'
    # specify container name and namespace
    $ py.test --hosts='kubectl://somepod-2536ab?container=nginx&namespace=web'


winrm
~~~~~

The winrm backend uses `pywinrm <https://pypi.python.org/pypi/pywinrm>`_::

    $ py.test --hosts='winrm://Administrator:Password@127.0.0.1'
    $ py.test --hosts='winrm://vagrant@127.0.0.1:2200?no_ssl=true&no_verify_ssl=true'

pywinrm's default read and operation timeout can be overridden using query
arguments ``read_timeout_sec`` and ``operation_timeout_sec``::

    $ py.test --hosts='winrm://vagrant@127.0.0.1:2200?read_timeout_sec=120&operation_timeout_sec=100'

LXC/LXD
~~~~~~~

The LXC backend can be used to test *running* LXC or LXD containers. It uses the
`lxc exec <https://linuxcontainers.org/lxd/getting-started-cli/>`_ command::

    $ py.test --hosts='lxc://container_name'
