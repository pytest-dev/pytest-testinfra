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

STATUS = [
    "STOPPED", "STARTING", "RUNNING", "BACKOFF", "STOPPING", "EXITED",
    "FATAL", "UNKNOWN",
]


class Supervisor(Module):
    """Test supervisor managed services

    >>> gunicorn = host.supervisor("gunicorn")
    >>> gunicorn.status
    'RUNNING'
    >>> gunicorn.is_running
    True
    >>> gunicorn.pid
    4242
    """

    def __init__(self, name, _attrs_cache=None):
        self.name = name
        self._attrs_cache = _attrs_cache
        super().__init__()

    @staticmethod
    def _parse_status(line):
        splitted = line.split()
        name = splitted[0]
        status = splitted[1]
        # supervisorctl exit status is 0 even if it cannot connect to
        # supervisord socket and output the error to stdout.
        # So we check that parsed status is a known status.
        if status not in STATUS:
            raise RuntimeError(
                "Cannot get supervisor status. Is supervisor running ?")
        if status == "RUNNING":
            pid = splitted[3]
            if pid[-1] == ",":
                pid = int(pid[:-1])
            else:
                pid = int(pid)
        else:
            pid = None
        return {"name": name, "status": status, "pid": pid}

    @property
    def _attrs(self):
        if self._attrs_cache is None:
            line = self.check_output("supervisorctl status %s", self.name)
            attrs = self._parse_status(line)
            assert attrs["name"] == self.name
            self._attrs_cache = attrs
        return self._attrs_cache

    @property
    def is_running(self):
        """Return True if managed service is in status RUNNING"""
        return self.status == "RUNNING"

    @property
    def status(self):
        """Return the status of the managed service

        Status can be STOPPED, STARTING, RUNNING, BACKOFF, STOPPING,
        EXITED, FATAL, UNKNOWN.

        See http://supervisord.org/subprocess.html#process-states
        """
        return self._attrs["status"]

    @property
    def pid(self):
        """Return the pid (as int) of the managed service"""
        return self._attrs["pid"]

    @classmethod
    def get_services(cls):
        """Get a list of services running under supervisor

        >>> host.supervisor.get_services()
        [<Supervisor(name="gunicorn", status="RUNNING", pid=4232)>
         <Supervisor(name="celery", status="FATAL", pid=None)>]
        """
        services = []
        for line in cls(None).check_output(
            "supervisorctl status",
        ).splitlines():
            attrs = cls._parse_status(line)
            service = cls(attrs["name"], attrs)
            services.append(service)
        return services

    def __repr__(self):
        return "<Supervisor(name=%s, status=%s, pid=%s)>" % (
            self.name,
            self.status,
            self.pid,
        )
