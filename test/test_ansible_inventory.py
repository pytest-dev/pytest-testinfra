import pytest

from testinfra.backend import parse_hostspec
from testinfra.utils.ansible_runner import expand_pattern, get_hosts, Inventory


@pytest.fixture
def inventory() -> Inventory:
    """Hosts are always under a group, the default is "ungrouped" if using the
    ini file format. The "all" meta-group always contains all hosts when
    expanded."""
    return {
        "_meta": {
            "hostvars": {
                "a": None,
                "b": None,
                "c": None,
            }
        },
        "all": {
            "children": ["nested"],
        },
        "left": {
            "hosts": ["a", "b"],
        },
        "right": {
            "hosts": ["b", "c"],
        },
        "combined": {
            "children": ["left", "right"],
        },
        "nested": {
            "children": ["combined"],
        }
    }


def test_expand_pattern_simple(inventory: Inventory):
    """Simple names are matched, recurring into groups if needed."""
    # direct hostname
    assert expand_pattern("a", inventory) == {"a"}
    # group
    assert expand_pattern("left", inventory) == {"a", "b"}
    # meta-group
    assert expand_pattern("combined", inventory) == {"a", "b", "c"}
    # meta-meta-group
    assert expand_pattern("nested", inventory) == {"a", "b", "c"}


def test_expand_pattern_fnmatch(inventory: Inventory):
    """Simple names are matched, recurring into groups if needed."""
    # l->left
    assert expand_pattern("l*", inventory) == {"a", "b"}
    # any single letter name
    assert expand_pattern("?", inventory) == {"a", "b", "c"}


def test_expand_pattern_regex(inventory: Inventory):
    """Simple names are matched, recurring into groups if needed."""
    # simple character matching - "l" matches "left" but not "all"
    assert expand_pattern("~l", inventory) == {"a", "b"}
    # "b" matches an exact host, not any group
    assert expand_pattern("~b", inventory) == {"b"}
    # "a" will match all
    assert expand_pattern("~a", inventory) == {"a", "b", "c"}


def test_get_hosts(inventory: Inventory):
    """Multiple names/patterns can be combined."""
    assert get_hosts("a", inventory) == ["a"]
    # the two pattern separators are handled
    assert get_hosts("a:b", inventory) == ["a", "b"]
    assert get_hosts("a,b", inventory) == ["a", "b"]
    # difference works
    assert get_hosts("left:!right", inventory) == ["a"]
    # intersection works
    assert get_hosts("left:&right", inventory) == ["b"]
    # intersection is taken with the intersection of the intersection groups
    assert get_hosts("all:&left:&right", inventory) == ["b"]
    # when the intersections ends up empty, so does the result
    assert get_hosts("all:&a:&c", inventory) == []
    # negation is taken with the union of negation groups
    assert get_hosts("all:!a:!c", inventory) == ["b"]


@pytest.mark.parametrize("left", ["h1", "!h1", "&h1", "~h1", "*h1"])
@pytest.mark.parametrize("sep", [":", ","])
@pytest.mark.parametrize("right", ["h2", "!h2", "&h2", "~h2", "*h2", ""])
def test_parse_hostspec(left: str, sep: str, right: str):
    """Ansible's host patterns are parsed without issue."""
    if right:
        pattern = f"{left}{sep}{right}"
    else:
        pattern = left
    assert parse_hostspec(pattern) == (pattern, {})
