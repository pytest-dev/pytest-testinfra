=========
Changelog
=========

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
