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

from __future__ import unicode_literals

from testinfra.modules.ansible import Ansible
from testinfra.modules.command import Command
from testinfra.modules.file import File
from testinfra.modules.group import Group
from testinfra.modules.interface import Interface
from testinfra.modules.mountpoint import MountPoint
from testinfra.modules.package import Package
from testinfra.modules.pip import PipPackage
from testinfra.modules.process import Process
from testinfra.modules.puppet import Facter
from testinfra.modules.puppet import PuppetResource
from testinfra.modules.salt import Salt
from testinfra.modules.service import Service
from testinfra.modules.socket import Socket
from testinfra.modules.sudo import Sudo
from testinfra.modules.supervisor import Supervisor
from testinfra.modules.sysctl import Sysctl
from testinfra.modules.systeminfo import SystemInfo
from testinfra.modules.user import User


__all__ = [
    "Command", "File", "Package", "Group", "Interface",
    "Service", "SystemInfo", "User", "Salt", "PuppetResource",
    "Facter", "Sysctl", "Socket", "Ansible", "Process",
    "Supervisor", "MountPoint", "Sudo", "PipPackage",
]
