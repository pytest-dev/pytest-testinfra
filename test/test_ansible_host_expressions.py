# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import tempfile

import pytest

from testinfra.utils.ansible_runner import AnsibleRunner

INVENTORY = b"""
---
group1:
  hosts:
    host1:
    host2:
group2:
  hosts:
    host3:
    host4:
group3:
  hosts:
    host1:
    host4:
group4:
   hosts:
    example1:
    example11:
    example2:
"""


@pytest.fixture(scope="module")
def get_hosts():
    with tempfile.NamedTemporaryFile() as f:
        f.write(INVENTORY)
        f.flush()

        def _get_hosts(spec):
            return AnsibleRunner(f.name).get_hosts(spec)

        yield _get_hosts


@pytest.fixture(scope="function")
def get_env_var():
    old_value = os.environ.get("ANSIBLE_INVENTORY")
    with tempfile.NamedTemporaryFile() as f:
        f.write(INVENTORY)
        f.flush()
        os.environ["ANSIBLE_INVENTORY"] = f.name

        def _get_env_hosts(spec):
            return AnsibleRunner(None).get_hosts(spec)

        yield _get_env_hosts
    if old_value:
        os.environ["ANSIBLE_INVENTORY"] = old_value
    else:
        del os.environ["ANSIBLE_INVENTORY"]


def test_ansible_host_expressions_index(get_hosts):
    assert get_hosts("group1(0)") == ["host1"]


def test_ansible_host_expressions_negative_index(get_hosts):
    assert get_hosts("group1(-1)") == ["host2"]


def test_ansible_host_expressions_not(get_hosts):
    assert get_hosts("group1,!group3") == ["host2"]


def test_ansible_host_expressions_and(get_hosts):
    assert get_hosts("group1,&group3") == ["host1"]


def test_ansible_host_complicated_expression(get_hosts):
    expression = "group1,group2,!group3,example1*"
    assert set(get_hosts(expression)) == {"host2", "host3", "example1", "example11"}


def test_ansible_host_regexp(get_hosts):
    with pytest.raises(ValueError):
        get_hosts("~example1*")


def test_ansible_host_with_ansible_inventory_env_var(get_env_var):
    assert set(get_env_var("host1,example1*")) == {"host1", "example1", "example11"}
