#########################
Contributing to testinfra
#########################

First, thanks for contributing to testinfra and make it even more awesome !

Pull requests
=============

Regardless the review by a developer, a pull request will trigger automatic
tests on these CI servers:

- https://travis-ci.org/philpep/testinfra/
- https://jenkins.philpep.org/job/testinfra/

You're encouraged to setup a full test environment, to add tests and check if
all the tests pass *before* submitting your pull request. To run the complete
test suite you must install:

- `Vagrant <https://vagrantup.com>`_ version 1.7 or greater
- `Docker <https://www.docker.com>`_ version 1.7 or greater
- `tox <https://tox.readthedocs.org/en/latest/>`_

To run all tests run::

    vagrant up --provider=docker
    tox

To speedup the docker images generation during `vagrant up` you can download
them before running the tests (docker will detect they are the same and use the
cache)::

    for tag in debian_jessie debian_wheezy centos_7 fedora_21 ubuntu_trusty; do
        docker pull philpep/testinfra:$tag
    done


Code style
==========

Your code must pass without errors under `flake8
<https://flake8.readthedocs.org>`_ with the extension `hacking
<http://docs.openstack.org/developer/hacking/>`_::


    pip install hacking
    flake8 testinfra
