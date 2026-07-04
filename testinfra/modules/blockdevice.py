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

import functools

from testinfra.modules.base import Module


class BlockDevice(Module):
    """Information for a block device.

    Should be used with sudo or under root.

    If the device is not a block device, RuntimeError is raised.
    """

    @property
    def _data(self):
        raise NotImplementedError

    def __init__(self, device):
        self.device = device
        self._dev_name = device.replace("/dev/", "")
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
        """Return True if the device is writable (have no RO status)

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
        raise ValueError(f"Unexpected value for rw: {mode}")

    @property
    def ra(self):
        """Return Read Ahead for the device in 512-bytes sectors.

        >>> host.block_device("/dev/sda").ra
        256
        """
        return self._data["read_ahead"]

    @property
    def is_zoned(self):
        """Return True if it is a zoned block device

        >>> host.block_device("/dev/sda").is_zoned
        True
        """
        return self.zoned_type != "none"
        
    @property
    def zoned(self):
        """Legacy property for zoned support"""
        return self.is_zoned

    @property
    def zoned_type(self):
        """Return Zoned Block Device type

         >>> host.block_device("/dev/sda").zoned_type
         'host-managed'
        """
        return self._data.get("zoned_type", "none")

    @property
    def zoned_chunk_sectors(self):
        return self._data.get("zoned_chunk_sectors", None)
        
    @property
    def zoned_nr_zones(self):
        return self._data.get("zoned_nr_zones", None)
        
    @property
    def zone_append_max_bytes(self):
        return self._data.get("zone_append_max_bytes", None)
        
    @property
    def max_open_zones(self):
        return self._data.get("max_open_zones", None)
        
    @property
    def max_active_zones(self):
        return self._data.get("max_active_zones", None)

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            return LinuxBlockDevice
        raise NotImplementedError

    def __repr__(self):
        return f"<BlockDevice(path={self.device})>"


class LinuxBlockDevice(BlockDevice):
    def _read_sysfs_attr(self, attr_name, convert=str):
        path = f"/sys/block/{self._dev_name}/queue/{attr_name}"
        f = self._host.file(path)
        if f.exists:
            val = f.content_string.strip()
            if val and val != "none":
                try:
                    return convert(val)
                except ValueError:
                    return val
        return None if convert != str else "none"

    @functools.cached_property
    def _data(self):
        header = ["RO", "RA", "SSZ", "BSZ", "StartSec", "Size", "Device"]
        command = "blockdev  --report %s"
        blockdev = self.run(command, self.device)
        if blockdev.rc != 0:
            raise RuntimeError(f"Failed to gather data: {blockdev.stderr}")
        output = blockdev.stdout.splitlines()
        if len(output) < 2:
            raise RuntimeError(f"No data from {self.device}")
        if output[0].split() != header:
            raise RuntimeError(f"Unknown output of blockdev: {output[0]}")
        fields = output[1].split()
        
        zoned_type = self._read_sysfs_attr("zoned") or "none"
        
        data = {
            "rw_mode": str(fields[0]),
            "read_ahead": int(fields[1]),
            "sector_size": int(fields[2]),
            "block_size": int(fields[3]),
            "start_sector": int(fields[4]),
            "size": int(fields[5]),
            "zoned_type": zoned_type,
        }
        
        if zoned_type != "none":
            chunk = self._read_sysfs_attr("chunk_sectors", int)
            if chunk is not None:
                data["zoned_chunk_sectors"] = chunk
                
            nr = self._read_sysfs_attr("nr_zones", int)
            if nr is not None:
                data["zoned_nr_zones"] = nr
                
            append = self._read_sysfs_attr("zone_append_max_bytes", int)
            if append is not None:
                data["zone_append_max_bytes"] = append
                
            open_z = self._read_sysfs_attr("max_open_zones", int)
            if open_z is not None:
                data["max_open_zones"] = open_z
                
            active_z = self._read_sysfs_attr("max_active_zones", int)
            if active_z is not None:
                data["max_active_zones"] = active_z

        return data