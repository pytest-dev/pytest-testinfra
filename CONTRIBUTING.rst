#########################
Contributing to testinfra
#########################

First, thanks for contributing to testinfra and make it even more awesome !

Pull requests
=============

You're encouraged to setup a full test environment, to add tests and check if
all the tests pass *before* submitting your pull request. To run the complete
test suite you must install:

- `Docker <https://www.docker.com>`_
- `tox <https://tox.readthedocs.io/en/latest/>`_

To run all tests run::

    tox

To run only some selected tests::

    # Only tests matching 'ansible' on 4 processes with pytest-xdist
    tox -- -v -n 4 -k ansible test

    # Only modules tests on a specific Python 3, e.g., 3.8 and spawn a pdb on error
    tox -e py38 -- -v --pdb test/test_modules.py


Code style
==========

Your code must pass without errors under `flake8
<https://flake8.readthedocs.io>`_ with the extension `hacking
<https://docs.openstack.org/hacking/latest/>`_::


    pip install hacking
    flake8 testinfra
