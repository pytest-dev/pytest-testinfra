all: test

test:
	py.test -vs --cov testinfra --cov-report term testinfra
	flake8 testinfra

doc:
	$(MAKE) -C doc html


.PHONY: all test doc
