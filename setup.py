#!/usr/bin/env python3
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

import setuptools


def local_scheme(version):
    """Generate a PEP440 compatible version if PEP440_VERSION is enabled"""
    import os
    import setuptools_scm.version  # only present during setup time

    return (
        ''
        if 'PEP440_VERSION' in os.environ
        else setuptools_scm.version.get_local_node_and_date(version)
    )


if __name__ == '__main__':
    setuptools.setup(
        use_scm_version={'local_scheme': local_scheme},
        setup_requires=["setuptools_scm"],
    )
