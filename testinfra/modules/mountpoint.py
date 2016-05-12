# -*- coding: utf-8 -*-
# Copyright © 2016 Philippe Pepiot, George Alton
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

from testinfra.modules.base import Module


class MountPoint(Module):
    """Test Mount Points"""

    def __init__(self, path):
        self._attrs = None
        self.path = path
        super(MountPoint, self).__init__()

    def _get_attrs(self):
        if self._attrs is None:
            self._attrs = self.get_mountpoint()
        return self._attrs

    def get_mountpoint(self):
        mountpoint = self.find_mountpoint()
        if mountpoint:
            return {
                "device": mountpoint[0],
                "filesystem": mountpoint[2],
                "options": mountpoint[3].split(",")
                }

    def __repr__(self):
        return "<mountpoint %s>" % (self.path,)

    def find_mountpoint(self):
        raise NotImplementedError

    @property
    def filesystem(self):
        """Returns the FileSystem type associated to a mount point

        >>> MountPoint("/").filesystem
        'ext4'

        """
        return self._get_attrs()["filesystem"]

    @property
    def device(self):
        """Return the device associated with a mount point

        >>> MountPoint("/").device
        '/dev/sda1'

        """
        return self._get_attrs()["device"]

    @property
    def exists(self):
        """Return if a mountpoint exists

        >>> MountPoint("/").exists
        True

        >>> MountPoint("/not/a/mountpoint").exists
        False

        """
        if self._get_attrs():
            return True

    @property
    def options(self):
        """Return a list of options that a mount point has been created with

        >>> MountPoint("/").options
        ['rw', 'relatime', 'data=ordered']

        """
        return self._get_attrs()["options"]

    @classmethod
    def get_module_class(cls, _backend):
        SystemInfo = _backend.get_module("SystemInfo")
        if SystemInfo.type == "linux":
            return LinuxMountPoint
        elif SystemInfo.type.endswith("bsd"):
            return BSDMountPoint
        else:
            raise NotImplementedError

    @classmethod
    def read_mounts(cls):
        raise NotImplementedError

    @classmethod
    def get_mountpoints(cls):
        """Returns a list of MountPoint instances

        >>> MountPoint.get_mountpoints()
        [<mountpoint />,  <mountpoint /proc>, <mountpoint /dev>]

        """
        raise NotImplementedError


class LinuxMountPoint(MountPoint):

    @classmethod
    def read_mounts(cls):
        return cls(None).check_output("cat /proc/self/mounts").splitlines()

    @classmethod
    def get_mountpoints(cls):
        return [cls(mountpoint.split()[1]) for mountpoint in cls.read_mounts()]

    def find_mountpoint(self):
        mounts = self.read_mounts()
        mount = [mount for mount in mounts if mount.split()[1] == self.path]

        # ignore rootfs
        # https://www.kernel.org/doc/Documentation/filesystems/ramfs-rootfs
        # -initramfs.txt
        # suggests that most OS mount the filesystem over it, leaving rootfs
        # would result in ambiguity when resolving a mountpoint
        devices_to_ignore = ["rootfs"]
        mount = [mnt for mnt in mount if mnt.split()[0] not in
                 devices_to_ignore]

        if mount:
            return mount[0].split()


class BSDMountPoint(MountPoint):

    @classmethod
    def read_mounts(cls):
        return cls(None).check_output("mount -p").splitlines()

    @classmethod
    def get_mountpoints(cls):
        return [cls(mountpoint.split()[1]) for mountpoint in cls.read_mounts()]

    def find_mountpoint(self):
        mounts = self.read_mounts()
        mount = [mount for mount in mounts if mount.split()[1] == self.path]

        if mount:
            return mount[0].split()
