import pytest
from testinfra.modules.python_package import PythonPackage

py_packages = """
alabaster (0.7.7)
Babel (2.2.0)
decorator (4.0.9)
docutils (0.12)
imagesize (0.7.0)
ipython (4.1.2)
ipython-genutils (0.1.0)
jedi (0.9.0)
Jinja2 (2.8)
MarkupSafe (0.23)
path.py (8.1.2)
pexpect (4.0.1)
pickleshare (0.6)
pip (8.0.2)
ptyprocess (0.5.1)
py (1.4.31)
Pygments (2.1.3)
pytest (2.9.1)
pytz (2016.3)
setuptools (19.6.2)
simplegeneric (0.8.1)
six (1.10.0)
snowballstemmer (1.2.1)
Sphinx (1.4)
testinfra (1.1.1, /home/tmacey/code/mit/ops/testinfra)
traitlets (4.2.1)
wheel (0.26.0)
"""

@pytest.mark.parametrize('package,version', [
    ('alabaster', '0.7.7'),
    ('docutils', '0.12')
])
def test_python_package_installed(package, version, monkeypatch):
    monkeypatch.setattr(PythonPackage, 'check_output',
                        lambda *args: py_packages)
    assert PythonPackage(package).is_installed
    assert PythonPackage(package).version == version


@pytest.mark.parametrize('package', [
    ('requests'),
])
def test_python_package_not_installed(package, monkeypatch):
    monkeypatch.setattr(PythonPackage, 'check_output',
                        lambda *args: py_packages)
    assert not PythonPackage(package).is_installed
