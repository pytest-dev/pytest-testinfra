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
import json

from testinfra.modules.base import Module


class BlockDevice(Module):
    """Information for block device.

    Should be used with sudo or under root.

    If device is not a block device, RuntimeError is raised.
    """

    @property
    def _data(self):
        raise NotImplementedError

    def __init__(self, device, _data_cache=None):
        self.device = device
        self._data_cache = _data_cache
        super().__init__()

    @classmethod
    def _iter_blockdevices(cls):
        raise NotImplementedError

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
    def get_blockdevices(cls):
        """Returns a list of BlockDevice instances

        >>> host.block_device.get_blockevices()
        [<BlockDevice(path=/dev/sda)>,
         <BlockDevice(path=/dev/sda1)>]
        """
        blockdevices = []
        for device in cls._iter_blockdevices():
            blockdevices.append(cls(device["name"], device))
        return blockdevices

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            return LinuxBlockDevice
        raise NotImplementedError

    def __repr__(self):
        return "<BlockDevice(path={})>".format(self.device)


class LinuxBlockDevice(BlockDevice):
    @functools.cached_property
    def _data(self):
        if self._data_cache:
            return self._data_cache
        # -J Use JSON output format
        # -O Output all available columns
        # -b Print the sizes in bytes
        command = f"lsblk -JOb {self.device}"
        out = self.check_output(command)
        blockdevs = json.loads(out)["blockdevices"]
        if not blockdevs:
            raise RuntimeError(f"No data from {self.device}")
        # start sector is not available in older lsblk version,
        # but we can read it from SYSFS
        if "start" not in blockdevs[0]:
            blockdevs[0]["start"] = 0
            # checking if device has internal parent kernel device name
            if blockdevs[0]["pkname"]:
                try:
                    command = f"cat /sys/dev/block/{blockdevs[0]['maj:min']}/start"
                    out = self.check_output(command)
                    blockdevs[0]["start"] = int(out)
                except AssertionError:
                    blockdevs[0]["start"] = 0
        return blockdevs[0]

    @classmethod
    def _iter_blockdevices(cls):
        def children_generator(children_list):
            for child in children_list:
                if "start" not in child:
                    try:
                        cmd = f"cat /sys/dev/block/{child['maj:min']}/start"
                        out = check_output(cmd)
                        child["start"] = int(out)
                    # At this point, the AssertionError only indicates that
                    # the device is a virtual block device (device mapper target).
                    # It can be assumed that the start sector is 0.
                    except AssertionError:
                        child["start"] = 0
                if "children" in child:
                    yield from children_generator(child["children"])
                yield child

        command = "lsblk -JOb"
        check_output = cls(None).check_output
        blockdevices = json.loads(check_output(command))["blockdevices"]
        for device in blockdevices:
            if "start" not in device:
                # Parent devices always start from 0
                device["start"] = 0
            if "children" in device:
                yield from children_generator(device["children"])
            yield device

    @property
    def is_partition(self):
        return self._data["type"] == "part"

    @property
    def sector_size(self):
        return self._data["log-sec"]

    @property
    def block_size(self):
        return self._data["phy-sec"]

    @property
    def start_sector(self):
        if self._data["start"]:
            return self._data["start"]
        return 0

    @property
    def is_writable(self):
        if self._data["ro"] == 0:
            return True
        return False

    @property
    def ra(self):
        return self._data["ra"]

    @property
    def is_removable(self):
        """Return True if device is removable

        >>> host.block_device("/dev/sda").is_removable
        False

        """
        return self._data["rm"]

    @property
    def hctl(self):
        """Return Host:Channel:Target:Lun for SCSI

        >>> host.block_device("/dev/sda").hctl
        '1:0:0:0'

        >>> host.block_device("/dev/nvme1n1").hctl
        None

        """
        return self._data["hctl"]

    @property
    def model(self):
        """Return device identifier

        >>> host.block_device("/dev/nvme1n1").model
        'Samsung SSD 970 EVO Plus 500GB'

        >>> host.block_device("/dev/nvme1n1p1").model
        None

        """
        return self._data["model"]

    @property
    def state(self):
        """Return state of the device

        >>> host.block_device("/dev/nvme1n1").state
        'live'

        >>> host.block_device("/dev/nvme1n1p1").state
        None

        """
        return self._data["state"]

    @property
    def partition_type(self):
        """Return partition table type

        >>> host.block_device("/dev/nvme1n1p1").partition_type
        'gpt'

        >>> host.block_device("/dev/nvme1n1").partition_type
        None

        """
        return self._data["pttype"]

    @property
    def wwn(self):
        """Return unique storage identifier

        >>> host.block_device("/dev/nvme1n1").wwn
        'eui.00253856a5ebaa6f'

        >>> host.block_device("/dev/nvme1n1p1").wwn
        'eui.00253856a5ebaa6f'

        """
        return self._data["wwn"]

    @property
    def filesystem_type(self):
        """Return filesystem type

        >>> host.block_device("/dev/nvme1n1p1").filesystem_type
        'vfat'

        >>> host.block_device("/dev/nvme1n1").filesystem_type
        None

        """
        return self._data["fstype"]

    @property
    def is_mounted(self):
        """Return True if the device is mounted

        >>> host.block_device("/dev/nvme1n1p1").is_mounted
        True

        """
        return bool(self._data["mountpoint"])

    @property
    def type(self):
        """Return device type

        >>> host.block_device("/dev/nvme1n1").type
        'disk'

        >>> host.block_device("/dev/nvme1n1p1").type
        'part'

        >>> host.block_device("/dev/mapper/vg-lvol0").type
        'lvm'

        """
        return self._data["type"]

    @property
    def transport_type(self):
        """Return device transport type

        >>> host.block_device("/dev/nvme1n1p1").transport_type
        'nvme'

        >>> host.block_device("/dev/sdc").transport_type
        'iscsi'

        """
        return self._data["tran"]
