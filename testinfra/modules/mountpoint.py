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

    @property
    def type(self):
        """ Returns the FileSystem type associated to a mount point
        >>> MountPoint("/").type
        'ext4'

        """
        raise NotImplementedError

    @property
    def device(self):
        """ Return the device associated with a mount point
        >>> MountPoint("/").device
        '/dev/sda1'
        """
        raise NotImplementedError

    @property
    def exists(self):
        """ Return if a mountpoint exists

        >>> MountPoint("/").exists
        True

        """
        raise NotImplementedError

    @property
    def options(self):
        """ Return a list of options that a mount point has been created with

        >>> MountPoint("/").options
        ['rw', 'relatime', 'data=ordered']
        """
        raise NotImplementedError

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

    # /proc/mounts
    # Before kernel 2.4.19, this file was a list of all the
    # filesystems currently mounted on the system.  With the
    # introduction of per-process mount namespaces in Linux 2.4.19,
    # this file became a link to /proc/self/mounts, which lists the
    # mount points of the process's own mount namespace.

    # format of /proc/self/mounts is documented at
    # http://man7.org/linux/man-pages/man5/fstab.5.html

    def find_mountpoint(self):
        mounts = self.check_output("cat /proc/self/mounts").splitlines()
        mount = [mount for mount in mounts if mount.split()[1] == self.path]

        # ignore rootfs
        # https://www.kernel.org/doc/Documentation/filesystems/ramfs-rootfs
        # -initramfs.txt
        # suggests that most OS mount the filesystem over it, leaving rootfs
        # would result in ambiguity when resolving a mountpoint
        mount = [mnt for mnt in mount if mnt[0] != "rootfs"]

        if mount:
            return mount[0]

    @property
    def type(self):
        mountpoint = self.find_mountpoint()
        if mountpoint:
            return mountpoint.split()[1]

    @property
    def device(self):
        mountpoint = self.find_mountpoint()
        if mountpoint:
            return mountpoint.split()[0]

    @property
    def exists(self):
        mountpoint = self.find_mountpoint()
        if mountpoint:
            return True

    @property
    def options(self):
        mountpoint = self.find_mountpoint()
        if mountpoint:
            return mountpoint[3].split(",")


class BSDMountPoint(MountPoint):
    pass
