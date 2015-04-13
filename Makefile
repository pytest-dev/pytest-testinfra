all: test

test:
	testinfra -vs --cov testinfra --cov-report term testinfra
	flake8 testinfra

doc:
	$(MAKE) -C doc html


.PHONY: all test doc
