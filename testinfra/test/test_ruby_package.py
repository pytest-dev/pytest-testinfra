import pytest
from testinfra.modules.ruby_package import RubyPackage

ruby_packages = """*** LOCAL GEMS ***

bigdecimal (1.2.8)
bundler (1.11.2)
did_you_mean (1.0.0)
io-console (0.4.5)
json (1.8.3)
minitest (5.8.3)
net-telnet (0.1.1)
power_assert (0.2.6)
psych (2.0.17)
rake (10.4.2)
rdoc (4.2.1)
test-unit (3.1.5)4"""

@pytest.mark.parametrize('package,version', [
    ('bundler', '1.11.2'),
    ('minitest', '5.8.3')
])
def test_ruby_package_installed(package, version, monkeypatch):
    monkeypatch.setattr(RubyPackage, 'check_output',
                        lambda *args: ruby_packages)
    assert RubyPackage(package).is_installed
    assert RubyPackage(package).version == version


@pytest.mark.parametrize('package', [
    ('requests'),
])
def test_ruby_package_not_installed(package, monkeypatch):
    monkeypatch.setattr(RubyPackage, 'check_output',
                        lambda *args: ruby_packages)
    assert not RubyPackage(package).is_installed
