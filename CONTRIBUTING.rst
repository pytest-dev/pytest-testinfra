#########################
Contributing to testinfra
#########################

First, thanks for contributing to testinfra and make it even more awesome !

Pull requests
=============

Regardless the review by a developer, a pull request will trigger automatic
tests on https://travis-ci.org/philpep/testinfra/

You're encouraged to setup a full test environment, to add tests and check if
all the tests pass *before* submitting your pull request. To run the complete
test suite you must install:

- `Docker <https://www.docker.com>`_
- `tox <https://tox.readthedocs.io/en/latest/>`_

To run all tests run::

    tox

To run only some selected tests::

    # Only tests matching 'ansible' on 4 processes with pytest-xdist
    tox -- -v -n 4 -k ansible

    # Only modules tests on python 2.7 and spawn a pdb on error
    tox -e py27 -- -v --pdb testinfra/test/test_modules.py


Code style
==========

Your code must pass without errors under `flake8
<https://flake8.readthedocs.io>`_ with the extension `hacking
<http://docs.openstack.org/developer/hacking/>`_::


    pip install hacking
    flake8 testinfra
