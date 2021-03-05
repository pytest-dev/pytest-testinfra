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

from testinfra.modules.base import Module
from testinfra.utils import cached_property


class BlockDevice(Module):
    """Information for block device.

    Should be used with sudo or under root.

    If device is not a block device, RuntimeError is raised.
    """

    @property
    def _data(self):
        raise NotImplementedError

    def __init__(self, device):
        self.device = device
        super().__init__()

    @property
    def is_partition(self):
        """Return True if the device is a partition.

        >>> host.block_device("/dev/sda1").is_partition
        True

        >>> host.block_device("/dev/sda").is_partition
        False


        """
        return self._data["start_sector"] > 0

    @property
    def size(self):
        """Return size if the device in bytes.

        >>> host.block_device("/dev/sda1").size
        512110190592

        """
        return self._data["size"]

    @property
    def sector_size(self):
        """Return sector size for the device in bytes.

        >>> host.block_device("/dev/sda1").sector_size
        512
        """
        return self._data["sector_size"]

    @property
    def block_size(self):
        """Return block size for the device in bytes.

        >>> host.block_device("/dev/sda").block_size
        4096
        """
        return self._data["block_size"]

    @property
    def start_sector(self):
        """Return start sector of the device on the underlying device.

           Usually the value is zero for full devices and is non-zero
           for partitions.

        >>> host.block_device("/dev/sda1").start_sector
        2048

        >>> host.block_device("/dev/md0").start_sector
        0
        """
        return self._data["sector_size"]

    @property
    def is_writable(self):
        """Return True if device is writable (have no RO status)

        >>> host.block_device("/dev/sda").is_writable
        True

        >>> host.block_device("/dev/loop1").is_writable
        False
        """
        mode = self._data["rw_mode"]
        if mode == "rw":
            return True
        if mode == "ro":
            return False
        raise ValueError("Unexpected value for rw: {}".format(mode))

    @property
    def ra(self):
        """Return Read Ahead for the device in 512-bytes sectors.

        >>> host.block_device("/dev/sda").ra
        256
        """
        return self._data["read_ahead"]

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            return LinuxBlockDevice
        raise NotImplementedError

    def __repr__(self):
        return "<BlockDevice(path={})>".format(self.device)


class LinuxBlockDevice(BlockDevice):
    @cached_property
    def _data(self):
        header = ["RO", "RA", "SSZ", "BSZ", "StartSec", "Size", "Device"]
        command = "blockdev  --report %s"
        blockdev = self.run(command, self.device)
        if blockdev.rc != 0 or blockdev.stderr:
            raise RuntimeError("Failed to gather data: {}".format(blockdev.stderr))
        output = blockdev.stdout.splitlines()
        if len(output) < 2:
            raise RuntimeError("No data from {}".format(self.device))
        if output[0].split() != header:
            raise RuntimeError("Unknown output of blockdev: {}".format(output[0]))
        fields = output[1].split()
        return {
            "rw_mode": str(fields[0]),
            "read_ahead": int(fields[1]),
            "sector_size": int(fields[2]),
            "block_size": int(fields[3]),
            "start_sector": int(fields[4]),
            "size": int(fields[5]),
        }
