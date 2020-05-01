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

from testinfra.modules.base import InstanceModule


def int_or_float(value):
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


class _Process(dict):

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            attrs = self["_get_process_attribute_by_pid"](self["pid"], key)
            if attrs["lstart"] != self["lstart"]:
                raise RuntimeError((
                    "Process with pid %s start time changed from %s to %s."
                    " This mean the process you are working on does not not "
                    "exist anymore"
                ) % (self["pid"], self["lstart"], attrs["lstart"]))
            return attrs[key]

    def __repr__(self):
        return "<process %s (pid=%s)>" % (self["comm"], self["pid"])


class Process(InstanceModule):
    """Test Processes attributes

    Processes are selected using ``filter()`` or ``get()``, attributes names
    are described in the `ps(1) man page
    <http://man7.org/linux/man-pages/man1/ps.1.html#STANDARD_FORMAT
    SPECIFIERS>`_.

    >>> master = host.process.get(user="root", comm="nginx")
    # Here is the master nginx process (running as root)
    >>> master.args
    'nginx: master process /usr/sbin/nginx -g daemon on; master_process on;'
    # Here are the worker processes (Parent PID = master PID)
    >>> workers = host.process.filter(ppid=master.pid)
    >>> len(workers)
    4
    # Nginx don't eat memory
    >>> sum([w.pmem for w in workers])
    0.8
    # But php does !
    >>> sum([p.pmem for p in host.process.filter(comm="php5-fpm")])
    19.2

    """

    def filter(self, **filters):
        """Get a list of matching process

        >>> host.process.filter(user="root", comm="zsh")
        [<process zsh (pid=2715)>, <process zsh (pid=10502)>, ...]
        """
        match = []
        for attrs in self._get_processes(**filters):
            for key, value in filters.items():
                if str(attrs[key]) != str(value):
                    break
            else:
                attrs["_get_process_attribute_by_pid"] = (
                    self._get_process_attribute_by_pid)
                match.append(_Process(attrs))
        return match

    def get(self, **filters):
        """Get one matching process

        Raise ``RuntimeError`` if no process found or multiple process
        matching filters.
        """
        matches = self.filter(**filters)
        if not matches:
            raise RuntimeError("No process found")
        if len(matches) > 1:
            raise RuntimeError("Multiple process found: %s" % (matches,))
        return matches[0]

    def _get_processes(self, **filters):
        raise NotImplementedError

    def _get_process_attribute_by_pid(self, pid, name):
        raise NotImplementedError

    @classmethod
    def get_module_class(cls, host):
        if host.file("/bin/ps").linked_to == "/bin/busybox":
            return BusyboxProcess
        if (host.system_info.type == "linux"
                or host.system_info.type.endswith("bsd")):
            return PosixProcess
        raise NotImplementedError

    def __repr__(self):
        return "<process>"


class PosixProcess(Process):
    # Should be portable on both Linux and BSD

    def _get_processes(self, **filters):
        cmd = "ps -Aww -o %s"
        attributes = {"pid", "comm", "pcpu", "pmem"} | set(filters.keys())

        # Theses attributes contains spaces. Put them at the end of the list
        attributes -= {"lstart", "args"}
        attributes = sorted(attributes)
        attributes.extend(["lstart", "args"])
        arg = ":50,".join(attributes)

        procs = []
        # skip first line (header)
        for line in self.check_output(cmd, arg).splitlines()[1:]:
            splitted = line.split()
            attrs = {}
            i = 0
            for i, key in enumerate(attributes[:-2]):
                attrs[key] = int_or_float(splitted[i])
            attrs["lstart"] = " ".join(splitted[i+1:i+6])
            attrs["args"] = " ".join(splitted[i+6:])
            procs.append(attrs)
        return procs

    def _get_process_attribute_by_pid(self, pid, name):
        out = self.check_output(
            "ps -ww -p %s -o lstart,%s", str(pid), name)
        splitted = out.splitlines()[1].split()
        return {
            "lstart": " ".join(splitted[:5]),
            name: int_or_float(splitted[5]),
        }


class BusyboxProcess(Process):

    def _get_processes(self, **filters):
        cmd = "ps -A -o %s"
        attributes = {"pid", "comm", "time"} | set(filters.keys())

        # Theses attributes contains spaces. Put them at the end of the list
        attributes -= {"args"}
        attributes = sorted(attributes)
        attributes.extend(["args"])
        arg = ",".join(attributes)

        procs = []
        # skip first line (header)
        for line in self.check_output(cmd, arg).splitlines()[1:]:
            splitted = line.split()
            attrs = {}
            i = 0
            for i, key in enumerate(attributes[:-1]):
                attrs[key] = int_or_float(splitted[i])

            attrs["lstart"] = attrs["time"]
            attrs["args"] = " ".join(splitted[i+1:])
            procs.append(attrs)

        return procs

    def _get_process_attribute_by_pid(self, pid, name):
        out = self.check_output("ps -o pid,time,%s", name)

        # skip first line (header)
        for line in out.splitlines()[1:]:
            splitted = line.split()
            if int(splitted[0]) == pid:
                return {
                    "lstart": splitted[1],
                    name: int_or_float(splitted[2]),
                }
