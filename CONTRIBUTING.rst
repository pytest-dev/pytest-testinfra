#########################
Contributing to testinfra
#########################

First thanks for contributing to testinfra and make it even more awesome !

Pull requests
=============

Regardless the review by a developer, a pull request will trigger automatic tests:

- https://travis-ci.org/philpep/testinfra/ basic tests
- https://jenkins.philpep.org/job/testinfra/ full test suite

You're encouraged to setup a full test environment, to add tests and check if
all the tests pass *before* submitting your pull request. To run the complete
test suite you must install:

- `Vagrant <https://vagrantup.com>`_ version 1.7.4 or greater
- `Docker <https://www.docker.com>`_ version 1.8.0 or greater
- `tox <https://tox.readthedocs.org/en/latest/>`_

To run all tests, just run `tox`.

To speedup the docker images generation you can download them before running the tests::

    for tag in debian_jessie debian_wheezy centos_7 fedora_21 ubuntu_trusty; do
        docker pull philpep/testinfra:$tag
    done


Code style
==========

Your code must pass without errors under `flake8
<https://flake8.readthedocs.org>`_ with the extension `hacking
<http://docs.openstack.org/developer/hacking/>`_.


::
    pip install hacking
    flake8 testinfra
