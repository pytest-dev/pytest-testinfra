all: test

test:
	testinfra -vs --cov testinfra --cov-report term testinfra
	flake8 testinfra

integration-test:
	vagrant up
	vagrant ssh-config > .vagrant/ssh_config
	testinfra -vs --cov testinfra --cov-report term --integration --ssh-config=.vagrant/ssh_config -n 4 testinfra

doc:
	$(MAKE) -C doc html


.PHONY: all test doc integration-test
