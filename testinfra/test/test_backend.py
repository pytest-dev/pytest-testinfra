import pytest
from testinfra import backend


def test_get_backend():
    assert backend.get_backend("local")
    assert backend.get_backend("testinfra.backend.local.Backend")

    with pytest.raises(RuntimeError):
        backend.get_backend("fake")
        backend.get_backend("testinfra.backend.fake.Backend")
