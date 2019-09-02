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

from testinfra.modules.base import Module


class BlockDevice(Module):
    """Information for block device.

       Should be used with sudo or under root.
    """

    def __init__(self, device):
        self.device = device
        self._data_cache = None
        super(BlockDevice, self).__init__()

    @classmethod
    def _probe_device(cls, device):
        raise NotImplementedError

    @property
    def is_block_device(self):
        """Return True if the device is a proper block device.

        Proper block device:
        * is a device which can report block device size (GETSIZE64)
        * size is greater than zero

        >>> host.block_device("/dev/sda5").is_block_device
        True

        >>> host.block_device("/dev/console").is_block_device
        False

        """
        is_proper = self._data['is_block_device'] and \
            self._data['size'] > 0

        return is_proper

    @property
    def is_partition(self):
        """Return True if the device is a partition.

        >>> host.block_device("/dev/sda1").is_partition
        True

        >>> host.block_device("/dev/sda").is_partition
        False

        """
        return self.is_block_device and self._data['start_sector'] > 0

    @property
    def size(self):
        """Return size if the device in bytes.

           Return None if device is not a block device.

        >>> host.block_device("/dev/sda1").size
        512110190592

        >>> print(host.block_device("/dev/console").size)
        None

        """
        if not self.is_block_device:
            return None
        return self._data['size']

    @property
    def sector_size(self):
        """Return sector size for the device in bytes or None.

        >>> host.block_device("/dev/sda1").sector_size
        512

        >>> print(host.block_device("/dev/console").sector_size)
        None

        """
        if not self.is_block_device:
            return None
        return self._data['sector_size']

    @property
    def block_size(self):
        """Return block size for the device in bytes or None.

        >>> host.block_device("/dev/sda").block_size
        4096

        >>> print(host.block_device("/dev/console").block_size)
        None

        """
        if not self.is_block_device:
            return None
        return self._data['block_size']

    @property
    def start_sector(self):
        """Return start sector of the device on the underlaying device.

           Usually the value is zero for full devices and is non-zero
           for partitions.
           Return None if device is not a block device.

        >>> host.block_device("/dev/sda1").start_sector
        2048

        >>> host.block_device("/dev/md0").start_sector
        0

        >>> print(host.block_device("/dev/console").start_sector)
        None

        """
        if not self.is_block_device:
            return None
        return self._data['sector_size']

    @property
    def is_writable(self):
        """Return True if device is writable (have no RO status), or None.

        >>> host.block_device("/dev/sda").is_writable
        True

        >>> host.block_device("/dev/loop1").is_writable
        False

        >>> host.block_device("/dev/console").is_writable
        None

        """
        if not self.is_block_device:
            return None
        mode = self._data['rw_mode']
        if mode == 'rw':
            return True
        if mode == 'ro':
            return False
        raise ValueError('Unexpected value for rw: %s' % mode)

    @property
    def ra(self):
        """Return Read Ahead for the device in 512-bytes sectors or None.

        >>> host.block_device("/dev/sda").ra
        256

        >>> print(host.block_device("/dev/console").ra)
        None
        """
        if not self.is_block_device:
            return None
        return self._data['read_ahead']

    @property
    def _data(self):
        if self._data_cache is None:
            self._data_cache = self._probe_device(self.device)
        return self._data_cache

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == 'linux':
            return LinuxBlockDevice
        # if host.system_info.type.endswith("bsd"):
        #     return BSDlockDevice
        raise NotImplementedError

    def __repr__(self):
        return '<BlockDevice(path=%s)>' % self.device


class LinuxBlockDevice(BlockDevice):

    @classmethod
    def _probe_device(cls, device):
        HEADER = ['RO', 'RA', 'SSZ', 'BSZ', 'StartSec', 'Size', 'Device']
        COMMAND = 'blockdev  --report %s'
        run = cls(None).run
        blockdev = run(COMMAND % device)
        if blockdev.rc != 0:
            return {
                'is_block_device': False,
                'rw_mode': None,
                'read_ahead': None,
                'sector_size': None,
                'block_size': None,
                'start_sector': None,
                'size': None
            }
        output = blockdev.stdout.splitlines()
        assert output[0].split() == HEADER, 'Unknown output of blkid'
        fields = output[1].split()
        return {
            'is_block_device': True,
            'rw_mode': str(fields[0]),
            'read_ahead': int(fields[1]),
            'sector_size': int(fields[2]),
            'block_size': int(fields[3]),
            'start_sector': int(fields[4]),
            'size': int(fields[5])
        }
