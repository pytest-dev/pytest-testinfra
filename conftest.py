# -*- coding: utf8 -*-
# Copyright © 2015 Philippe Pepiot
#
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

import uuid

import pytest


@pytest.fixture(scope="function")
def remote_tempdir(request, Command):
    dirname = "/tmp/testinfra-%s" % uuid.uuid4().hex
    assert Command("rm -rf %s; mkdir -p %s", dirname, dirname).rc == 0

    def fin():
        Command("rm -rf %s", dirname)

    request.addfinalizer(fin)
    return dirname


def pytest_addoption(parser):
    parser.addoption("--integration", action="store_true",
                     help="Run integration tests")


def pytest_runtest_setup(item):
    if (
        "integration" in item.keywords and
        not item.config.getoption("--integration")
    ):
        pytest.skip("integration test not selected")
