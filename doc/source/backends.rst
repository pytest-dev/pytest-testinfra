Connection backends
===================

Testinfra comes with several connections backends for remote command
execution.

When installing, you should select the backends you require as
``extras`` to ensure Python dependencies are satisfied (note various
system packaged tools may still be required).  For example ::

    $ pip install pytest-testinfra[ansible,salt]

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
<https://www.paramiko.org/>`_ is a Python implementation of the SSHv2
protocol. Testinfra will not ask you for a password, so you must be
able to connect without password (using passwordless keys or using
``ssh-agent``).

You can provide an alternate ssh-config::

    $ py.test --ssh-config=/path/to/ssh_config --hosts=server


docker
~~~~~~

The Docker backend can be used to test *running* Docker containers. It uses the
`docker exec <https://docs.docker.com/reference/commandline/exec/>`_ command::

    $ py.test --hosts='docker://[user@]container_id_or_name'

See also the :ref:`Test docker images` example.


podman
~~~~~~

The Podman backend can be used to test *running* Podman containers. It uses the
`podman exec <https://github.com/containers/libpod/blob/master/docs/source/markdown/podman.1.md>`_ command::

    $ py.test --hosts='podman://[user@]container_id_or_name'


ssh
~~~

This is a pure SSH backend using the ``ssh`` command. Example::

    $ py.test --hosts='ssh://server'
    $ py.test --ssh-config=/path/to/ssh_config --hosts='ssh://server'
    $ py.test --ssh-identity-file=/path/to/key --hosts='ssh://server'
    $ py.test --hosts='ssh://server?timeout=60&controlpersist=120'
    $ py.test --hosts='ssh://server' --ssh-extra-args='-o StrictHostKeyChecking=no'

By default timeout is set to 10 seconds and ControlPersist is set to 60 seconds.
You can disable persistent connection by passing `controlpersist=0` to the options.


salt
~~~~

The salt backend uses the `salt Python client API
<https://docs.saltstack.com/en/latest/ref/clients/>`_ and can be used from the salt-master server::

    $ py.test --hosts='salt://*'
    $ py.test --hosts='salt://minion1,salt://minion2'
    $ py.test --hosts='salt://web*'
    $ py.test --hosts='salt://G@os:Debian'

Testinfra will use the salt connection channel to run commands.

Hosts can be selected by using the `glob` and `compound matchers
<https://docs.saltstack.com/en/latest/topics/targeting/compound.html>`_.


.. _ansible connection backend:

ansible
~~~~~~~

Ansible inventories may be used to describe what hosts Testinfra should use
and how to connect them, using Testinfra's Ansible backend.

To use the Ansible backend, prefix the ``--hosts`` option with ``ansible://`` e.g::

    $ py.test --hosts='ansible://all' # tests all inventory hosts
    $ py.test --hosts='ansible://host1,ansible://host2'
    $ py.test --hosts='ansible://web*'

An inventory may be specified with the ``--ansible-inventory`` option, otherwise
the default (``/etc/ansible/hosts``) is used.

The ``ansible_connection`` value in your inventory will be used to determine
which backend to use for individual hosts: ``local``, ``ssh``, ``paramiko`` and ``docker``
are supported values. Other connections (or if you are using the ``--force-ansible``
option) will result in testinfra running all commands via Ansible itself,
which is substantially slower than the other backends::

    $ py.test --force-ansible --hosts='ansible://all'
    $ py.test --hosts='ansible://host?force_ansible=True'

By default, the Ansible connection backend will first try to use
``ansible_ssh_private_key_file`` and ``ansible_private_key_file`` to authenticate,
then fall back to the ``ansible_user`` with ``ansible_ssh_pass`` variables (both
are required), before finally falling back to your own host's SSH config.

This behavior may be overwritten by specifying either the ``--ssh-identity-file``
option or the ``--ssh-config`` option

Finally, these environment variables are supported and will be passed along to
their corresponding ansible variable (See Ansible documentation):

https://docs.ansible.com/ansible/2.3/intro_inventory.html

https://docs.ansible.com/ansible/latest/reference_appendices/config.html

* ``ANSIBLE_REMOTE_USER``
* ``ANSIBLE_SSH_EXTRA_ARGS``
* ``ANSIBLE_SSH_COMMON_ARGS``
* ``ANSIBLE_REMOTE_PORT``
* ``ANSIBLE_BECOME_USER``
* ``ANSIBLE_BECOME``

kubectl
~~~~~~~

The kubectl backend can be used to test containers running in Kubernetes.  It
uses the `kubectl exec <https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#exec/>`_ command and
support connecting to a given container name within a pod and using a given
namespace::

    # will use the default namespace and default container
    $ py.test --hosts='kubectl://mypod-a1b2c3'
    # specify container name and namespace
    $ py.test --hosts='kubectl://somepod-2536ab?container=nginx&namespace=web'
    # specify the kubeconfig context to use
    $ py.test --hosts='kubectl://somepod-2536ab?context=k8s-cluster-a&container=nginx'
    # you can specify kubeconfig either from KUBECONFIG environment variable
    # or when working with multiple configuration with the "kubeconfig" option
    $ py.test --hosts='kubectl://somepod-123?kubeconfig=/path/kubeconfig,kubectl://otherpod-123?kubeconfig=/other/kubeconfig'

openshift
~~~~~~~~~

The openshift backend can be used to test containers running in OpenShift.  It
uses the `oc exec <https://docs.openshift.com/container-platform/4.2/nodes/containers/nodes-containers-remote-commands.html>`_ command and
support connecting to a given container name within a pod and using a given
namespace::

    # will use the default namespace and default container
    $ py.test --hosts='openshift://mypod-a1b2c3'
    # specify container name and namespace
    $ py.test --hosts='openshift://somepod-2536ab?container=nginx&namespace=web'
    # you can specify kubeconfig either from KUBECONFIG environment variable
    # or when working with multiple configuration with the "kubeconfig" option
    $ py.test --hosts='openshift://somepod-123?kubeconfig=/path/kubeconfig,openshift://otherpod-123?kubeconfig=/other/kubeconfig'

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
