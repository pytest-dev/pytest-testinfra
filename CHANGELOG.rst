=========
Changelog
=========

3.0.4
=====

* Add support for ansible lxc and lxd connections

3.0.3
=====

* Fix paramiko parsing RequestTTY from ssh configs
* Re-add "groups" key from ansible.get_variables() to be backward compatible
  with testinfra 2.X

3.0.2
=====

* Fix ansible with no inventory resolving to "localhost"
* Fix support for ansible 2.8 with no inventory
* Fix ansible/paramiko which wasn't reading hosts config from ~/.ssh/config
* Allow to pass --ssh-config and --ssh-identity-file to ansible connection

3.0.1
=====

* Fix parsing of ipv6 adresses for paramiko, ssh and ansible backends.
* Fix --connection=ansible invocation when no hosts are provided

3.0.0
=====

* New ansible backend fixing support for ansible 2.8 and license issue. See
  https://github.com/philpep/testinfra/issues/431 for details. This make
  ansible using testinfra native backends and only works for local, ssh or
  docker connections. I you have others connection types or issues, please open
  a bug on https://github.com/philpep/testinfra/issues/new
* Windows support is improved. "package" module is handled with Chocolatey and
  there's support for the "user" module.


2.1.0
======

* docker: new get_containers() classmethod
* socket: fix parsing of ipv6 addresses with new versions of ss
* service: systemd fallback to sysv when "systemctl is-active" is not working

2.0.0
======

* Add addr module, used to test network connectivity
* Drop deprecated "testinfra" command, you should use "py.test" instead
* Drop deprecated top level fixtures, access them through the fixture "host" instead.
* Drop support for ansible <= 2.4

1.19.0
======

* Add docker module
* Fix pytest 4 compatibility

1.18.0
======

* Allow to urlencode character in host specification "user:pass@host" (#387)
* Fix double logging from both pytest and testinfra
* Drop support for python 2.6
* Allow to configure timeouts for winrm backend

1.17.0
======

* Add support for ansible "become" user in ansible module
* Add failed/suceeded property on run() output

1.16.0
======

* packaging: Use setuptools_scm instead of pbr
* iptables: add ip6tables support
* sysctl: find sysctl outside of PATH (/sbin)

1.15.0
======

* Fix finding ss and netstat command in "sbin" paths for Centos (359)
* Add a workaround for https://github.com/pytest-dev/pytest/issues/3542
* Handle "starting" status for Service module on Alpine linux
* Fix no_ssl and no_verify_ssl options for WinRM backend

1.14.1
======

* Fix multi-host test ordering (#347), regression introduced in 1.13.1
* Fix Socket on OpenBSD hosts (#338)

1.14.0
======

* Add a new lxc backend
* Socket: fix is_listening for unix sockets
* Add namespace and container support for kubernetes backend
* Add a cache of parsed ansible inventories for ansible backend
* Service: fix service detection on Centos 6 hosts
* File: implement file comparison with string paths

1.13.1
======

* package: fix is_installed and version behavior for uninstalled packages (#321 and #326)
* ansible: Use predictibles test ordering when using pytest-xdist to fix random test collections errors (#316)

1.13.0
======

* socket: fix detection of udp listening sockets (#311)
* ssh backend: Add support for GSSAPI

1.12.0
======

* ansible: fix compatibility with ansible 2.5
* pip: fix compatibility with pip 10 (#299)

1.11.1
======

* Socket: fix error with old versions of ss without the --no-header option (#293)

1.11.0
======

* Fix bad error reporting when using ansible module without ansible backend (#288)
* Socket: add a new implementation using ss instead of netstat (#124)
* Add service, process, and systeminfo support for Alpine (#283)

1.10.1
======

* Fix get_variables() for ansible>=2.0,<2.4 (#274)
* Paramiko: Use the RequireTTY setting if specified in a provided SSHConfig (#247)

1.10.0
======

* New iptables module

1.9.1
=====

* Fix running testinfra within a suite using doctest (#268)
* Service: add is_valid method for systemd
* Fix file.linked_to() for Mac OS

1.9.0
=====

* Interface: allow to find 'ip' command ousite of PATH
* Fix --nagios option with python 3

1.8.0
=====

* Deprecate testinfra command (will be dropped in 2.0), use py.test instead #135
* Handle --nagios option when using py.test command

1.7.1
=====

* Support for ansible 2.4 (#249)

1.7.0
=====

* Salt: allow specifiy config directory (#230)
* Add a WinRM backend
* Socket: ipv6 sockets can handle ipv4 clients (#234)
* Service: Enhance upstart detection (#243)

1.6.5
=====

* Service: add is_enabled() support for OpenBSD
* Add ssh identity file option for paramiko and ssh backends
* Expand tilde (~) to user home directory for ssh-config, ssh-identity-file and
  ansible-inventory options

1.6.4
=====

* Service: Allow to find 'service' command outside of $PATH #211
* doc fixes

1.6.3
=====

* Fix unwanted deprecation warning when running tests with pytest 3.1 #204

1.6.2
=====

* Fix wheel package for 1.6.1

1.6.1
=====

* Support ansible 2.3 with python 3 (#197)

1.6.0
=====

* New 'host' fixture as a replacement for all other fixtures.
  See https://testinfra.readthedocs.io/en/latest/modules.html#host
  (Other fixtures are deprecated and will be removed in 2.0 release).


1.5.5
=====

* backends: Fix ansible backend with ansible >= 2.3 (#195)

1.5.4
=====

* backends: fallback to UTF-8 encoding when system encoding is ASCII.
* Service: fix is_running() on systems using Upstart

1.5.3
=====

* Sudo: restore backend command in case of exceptions

1.5.2
=====

* Honnor become_user when using the ansible backend

1.5.1
=====

* Add dependency on importlib on python 2.6


1.5.0
=====

* New kubectl backend
* Command: check_output strip carriage return and newlines (#164)
* Package: rpm improve getting version() and release()
* User: add gecos (comment) field (#155)

1.4.5
=====

* SystemInfo: detect codename from VERSION_CODENAME in /etc/os-release
  (fallback when lsb_release isn't installed).
* Package: add release property for rpm based systems.
