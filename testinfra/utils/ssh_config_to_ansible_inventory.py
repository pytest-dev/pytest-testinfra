# -*- coding: utf8 -*-
# Copyright © 2015-2016 Philippe Pepiot
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

# pylint: disable=import-error

from __future__ import print_function

import fileinput
import sys

import ansible
import paramiko


def ssh_config_to_ansible_inventory():
    if len(sys.argv) >= 2:
        stream = fileinput.input([sys.argv[1]])
    else:
        stream = fileinput.input()

    ssh_config = paramiko.SSHConfig()
    ssh_config.parse(stream)

    ansible_major_version = int(ansible.__version__.split(".", 1)[0])
    if ansible_major_version == 1:
        key_map = {
            "hostname": "ansible_ssh_host",
            "user": "ansible_ssh_user",
            "port": "ansible_ssh_port",
            "identityfile": "ansible_ssh_private_key_file",
        }
    elif ansible_major_version == 2:
        key_map = {
            "hostname": "ansible_host",
            "user": "ansible_user",
            "port": "ansible_port",
            "identityfile": "ansible_ssh_private_key_file",
        }
    else:
        raise RuntimeError(
            "Ansible version {} not supported".format(ansible.__version__))

    for hostname in (e for e in ssh_config.get_hostnames() if e != "*"):
        items = [hostname]
        for key, value in ssh_config.lookup(hostname).items():
            if key in key_map:
                if key == "identityfile":
                    value = value[0]
                items.append("{}={}".format(key_map[key], value))
        print(" ".join(items))

if __name__ == "__main__":
    ssh_config_to_ansible_inventory()
