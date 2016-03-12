from __future__ import unicode_literals
from __future__ import absolute_import

from testinfra.backend import base


class LXDBackend(base.BaseBackend):
    NAME = "lxd"

    def __init__(self, container, *args, **kwargs):
        self.container = container
        super(LXDBackend, self).__init__(self.container, *args, **kwargs)

    def run(self, command, *args, **kwargs):
        command = self.get_command(command, *args)
        out = self.run_local("lxc exec %s --mode=non-interactive -- "
                             "/bin/sh -c %s",
                             self.container, command)
        out.command = self.encode(command)
        return out
