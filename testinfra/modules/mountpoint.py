# -*- coding: utf-8 -*-
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

from testinfra.modules.base import Module


class MountPoint(Module):
    """Test Mount Points"""

    def __init__(self, path):
        self.path = path
        super(MountPoint, self).__init__()

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
        mountpoint = self.find_mountpoint()
        if mountpoint:
            return mountpoint[2]

    @property
    def device(self):
        """Return the device associated with a mount point

        >>> MountPoint("/").device
        '/dev/sda1'
        """
        mountpoint = self.find_mountpoint()
        if mountpoint:
            return mountpoint[0]

    @property
    def exists(self):
        """Return if a mountpoint exists

        >>> MountPoint("/").exists
        True

        >>> MountPoint("/not/a/mountpoint").exists
        False

        """
        mountpoint = self.find_mountpoint()
        if mountpoint:
            return True

    @property
    def options(self):
        """Return a list of options that a mount point has been created with

        >>> MountPoint("/").options
        ['rw', 'relatime', 'data=ordered']
        """
        mountpoint = self.find_mountpoint()
        if mountpoint:
            return mountpoint[3].split(",")

    @classmethod
    def get_module_class(cls, _backend):
        SystemInfo = _backend.get_module("SystemInfo")
        if SystemInfo.type == "linux":
            return LinuxMountPoint
        elif SystemInfo.type.endswith("bsd"):
            return BSDMountPoint
        else:
            raise NotImplementedError


class LinuxMountPoint(MountPoint):

    def find_mountpoint(self):
        mounts = self.check_output("cat /proc/self/mounts").splitlines()
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

    def find_mountpoint(self):
        mounts = self.check_output("mount -p").splitlines()
        mount = [mount for mount in mounts if mount.split()[1] == self.path]

        if mount:
            return mount[0].split()
