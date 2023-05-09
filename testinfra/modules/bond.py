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

from testinfra.modules.interface import Interface, LinuxInterface


class Bond(Interface):
    """Test bond interface settings"""

    @property
    def mode(self):
        """Returns the mode as a tuple (name, index)
        >>> host.bond("bond0").mode
        ('balance-alb', 6)
        """
        raise NotImplementedError

    @property
    def slaves(self):
        """Alias for ports"""
        return self.ports

    @property
    def ports(self):
        """Returns a list of device names which are bonded
        >>> host.bond("bond0").ports
        ["eth0", "eth1"]
        """
        raise NotImplementedError

    @property
    def mii(self):
        """Returns mii monitoring interval and status
        >>> host.bond("bond0").mii()
        (100, up)
        >>> host.bond("bond1").mii()
        (200, down)
        """

        raise NotImplementedError

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            return LinuxBond

        raise NotImplementedError


class LinuxBond(Bond, LinuxInterface):
    def __init__(self, name, family=None):
        super().__init__(name, family)

    def _stat(self, name):
        return self.check_output(f"cat /sys/class/net/{self.name}/bonding/{name}")

    @property
    def ports(self):
        ports = self._stat("slaves")

        if ports:
            return ports.split(" ")
        else:
            return []

    @property
    def mode(self):
        stdout = self._stat("mode")

        # eg: balance-tlb 6
        mode, index = stdout.split(" ")
        return (mode, int(index))

    @property
    def mii(self):
        mii_delay = int(self._stat("miimon"))
        mii_state = self._stat("mii_status")

        return (mii_delay, mii_state)
