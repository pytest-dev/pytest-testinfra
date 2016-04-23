# -*- coding: utf8 -*-
# Copyright © 2016 Jimmy Tang <jimmy_tang@rapid7.com>
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


class Supervisor(Module):
    """Test supervisor managed processes"""

    def __init__(self, name):
        self.name = name
        super(Supervisor, self).__init__()

    @property
    def is_running(self):
        """Test if supervisord managed service is running"""
        return self.status(self.name) == "RUNNING"

    @property
    def is_stopped(self):
        """Test if supervisord managed service is stopped"""
        return self.status(self.name) == "STOPPED"

    def get_services(self):
        """Get services from supervisorctl and returns a dict"""
        ret = []
        output = self.check_output("supervisorctl status")
        for line in output.splitlines():
            name, status, _, pid, _, uptime = line.split()
            service = dict(
                    name=name,
                    status=status,
                    pid=pid,
                    uptime=uptime,
                    )
            ret.append(service)
        return ret

    def status(self, name):
        service = [ item for item in self.get_services() if item['name'] == name ]
        try:
            return service[0]['status']
        except IndexError as e:
            return 'NOTPRESENT'

    def __repr__(self):
        return "<service %s>" % (self.name,)
