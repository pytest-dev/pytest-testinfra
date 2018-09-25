#!/usr/bin/env python
# coding: utf-8
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
import setuptools

setuptools.setup(
    name='testinfra',
    author='Philippe Pepiot',
    author_email='phil@philpep.org',
    description='Test infrastructures',
    long_description=open(os.path.join(
        os.path.dirname(__file__), 'README.rst')).read(),
    url='https://github.com/philpep/testinfra',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Testing',
        'Topic :: System :: Systems Administration',
        'Framework :: Pytest',
    ],
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'testinfra = testinfra.main:main',
        ],
        'pytest11': {
            'pytest11.testinfra=testinfra.plugin',
        },
    },
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    install_requires=[
        'pytest!=3.0.2',
        'six>=1.4',
        "importlib; python_version=='2.6'",
    ],
)
