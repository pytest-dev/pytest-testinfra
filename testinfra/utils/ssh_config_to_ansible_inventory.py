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

import fileinput
import sys

try:
    import paramiko
except ImportError:
    HAS_PARAMIKO = False
else:
    HAS_PARAMIKO = True


def ssh_config_to_ansible_inventory():
    if not HAS_PARAMIKO:
        raise RuntimeError((
            "You must install paramiko package (pip install paramiko) "
            "to use ssh_config_to_ansible_inventory()"))

    if len(sys.argv) >= 2:
        stream = fileinput.input([sys.argv[1]])
    else:
        stream = fileinput.input()

    ssh_config = paramiko.SSHConfig()
    ssh_config.parse(stream)

    for hostname in (e for e in ssh_config.get_hostnames() if e != "*"):
        items = [hostname]
        for key, value in ssh_config.lookup(hostname).items():
            if key == "hostname":
                items.append("ansible_ssh_host=" + value)
            elif key == "user":
                items.append("ansible_ssh_user=" + value)
            elif key == "port":
                items.append("ansible_ssh_port=" + value)
            elif key == "identityfile":
                items.append("ansible_ssh_private_key_file=" + value[0])
        print(" ".join(items))

if __name__ == "__main__":
    ssh_config_to_ansible_inventory()
