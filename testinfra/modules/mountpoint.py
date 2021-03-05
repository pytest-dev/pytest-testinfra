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


class MountPoint(Module):
    """Test Mount Points"""

    def __init__(self, path, _attrs_cache=None):
        self.path = path
        self._attrs_cache = _attrs_cache
        super().__init__()

    @classmethod
    def _iter_mountpoints(cls):
        raise NotImplementedError

    @property
    def exists(self):
        """Return True if the mountpoint exists

        >>> host.mount_point("/").exists
        True

        >>> host.mount_point("/not/a/mountpoint").exists
        False

        """
        return bool(self._attrs)

    @property
    def _attrs(self):
        if self._attrs_cache is None:
            for mountpoint in self._iter_mountpoints():
                if mountpoint["path"] == self.path:
                    self._attrs_cache = mountpoint
                    break
            else:
                self._attrs_cache = {}
        return self._attrs_cache

    @property
    def filesystem(self):
        """Returns the filesystem type associated

        >>> host.mount_point("/").filesystem
        'ext4'

        """
        return self._attrs["filesystem"]

    @property
    def device(self):
        """Return the device associated

        >>> host.mount_point("/").device
        '/dev/sda1'

        """
        return self._attrs["device"]

    @property
    def options(self):
        """Return a list of options that a mount point has been created with

        >>> host.mount_point("/").options
        ['rw', 'relatime', 'data=ordered']

        """
        return self._attrs["options"]

    @classmethod
    def get_mountpoints(cls):
        """Returns a list of MountPoint instances

        >>> host.mount_point.get_mountpoints()
        [<MountPoint(path=/proc, device=proc, filesystem=proc, options=rw,nosuid,nodev,noexec,relatime)>
         <MountPoint(path=/, device=/dev/sda1, filesystem=ext4, options=rw,relatime,errors=remount-ro,data=ordered)>]
        """  # noqa
        mountpoints = []
        for mountpoint in cls._iter_mountpoints():
            mountpoints.append(cls(mountpoint["path"], mountpoint))
        return mountpoints

    @classmethod
    def get_module_class(cls, host):
        if host.system_info.type == "linux":
            return LinuxMountPoint
        if host.system_info.type.endswith("bsd"):
            return BSDMountPoint
        raise NotImplementedError

    def __repr__(self):
        return (
            "<MountPoint(path={}, device={}, filesystem={}, " "options={})>"
        ).format(
            self.path,
            self.device,
            self.filesystem,
            ",".join(self.options),
        )


class LinuxMountPoint(MountPoint):
    @classmethod
    def _iter_mountpoints(cls):
        check_output = cls(None).check_output
        for line in check_output("cat /proc/mounts").splitlines():
            splitted = line.split()
            # ignore rootfs
            # https://www.kernel.org/doc/Documentation/filesystems/ramfs-rootfs-initramfs.txt
            # suggests that most OS mount the filesystem over it, leaving
            # rootfs would result in ambiguity when resolving a mountpoint.
            if splitted[0] == "rootfs":
                continue

            yield {
                "path": splitted[1],
                "device": splitted[0],
                "filesystem": splitted[2],
                "options": splitted[3].split(","),
            }


class BSDMountPoint(MountPoint):
    @classmethod
    def _iter_mountpoints(cls):
        check_output = cls(None).check_output
        for line in check_output("mount -p").splitlines():
            splitted = line.split()
            yield {
                "path": splitted[1],
                "device": splitted[0],
                "filesystem": splitted[2],
                "options": splitted[3].split(","),
            }
