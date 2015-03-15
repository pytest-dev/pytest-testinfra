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

from __future__ import unicode_literals

from testinfra import run

import collections


SystemInfo = collections.namedtuple('SystemInfo', [
    'type', 'distribution', 'release', 'codename',
])


def get_system_info():
    sysinfo = {}
    kernel = run("uname -s")
    if kernel.rc == 0:
        sysinfo["type"] = kernel.stdout.splitlines()[0].lower()
    lsb = run("lsb_release -a")
    if lsb.rc == 0:
        for line in lsb.stdout.splitlines():
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip().lower()
            if key == "distributor id":
                sysinfo["distribution"] = value
            elif key == "release":
                sysinfo["release"] = value
            elif key == "codename":
                sysinfo["codename"] = value
    else:
        version = run("cat /etc/debian_version")
        if version.rc == 0:
            sysinfo["distribution"] = "debian"
            sysinfo["release"] = version.stdout.splitlines()[0]
    return SystemInfo(**sysinfo)
