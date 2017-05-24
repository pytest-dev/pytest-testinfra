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

import re

from functools import wraps
from testinfra.modules.base import Module


class ServiceProvider(object):

    @classmethod
    def provider(cls, host):
        raise NotImplementedError


class LinuxServiceProvider(ServiceProvider):

    @classmethod
    def provider(cls, host):
        if host.system_info.is_linux:

            if host.system_info.has_systemd:
                return SystemdService

            if host.system_info.is_redhat and host.system_info.has_service:
                return SysvService

            if host.system_info.has_initctl and host.exists('status'):
                return UpstartService

            return SysvService


class BSDServiceProvider(ServiceProvider):

    @classmethod
    def provider(cls, host):
        if host.system_info.is_bsd:

            if host.system_info.is_freebsd:
                return FreeBSDService

            if host.system_info.is_openbsd:
                return OpenBSDService

            if host.system_info.is_netbsd:
                return NetBSDService


class DarwinServiceProvider(ServiceProvider):

    @classmethod
    def provider(cls, host):
        if host.system_info.is_darwin:
            return LaunchdService


def providers(*providerz):
    '''
    This can be used as a decorator for @classmethods calls to simplify or override behavior.

    An example of how to use this decorator:

        # If applied to Service.get_module_class

            @classmethod
            @providers(
                LinuxServiceProvider,
                BSDServiceProvider,
                DarwinServiceProvider,
            )
            def get_module_class(cls, host):
                # the decorators listed in @providers will check to see if a service provider
                # can be found.
                #   If found:
                #       - Return the service provide from the decotor
                #
                #   If no provider is found, we just raise NotImplementedError
                raise NotImplementedError
    '''
    def wrapped_method(func):
        @wraps(func)
        def on_call(cls, host, *args, **kwargs):
            for provider_class in providerz:
                provider = provider_class.provider(host)
                if provider:
                    return provider
            return func(cls, host, *args, **kwargs)
        return on_call
    return wrapped_method


class Service(Module):
    """Test services

    Implementations:

    - Linux: detect Systemd or Upstart, fallback to SysV
    - FreeBSD: service(1)
    - OpenBSD: ``/etc/rc.d/$name check`` for ``is_running``
      (``is_enabled`` is not yet implemented)
    - NetBSD: ``/etc/rc.d/$name onestatus`` for ``is_running``
      (``is_enabled`` is not yet implemented)

    """

    def __init__(self, name):
        self.name = name
        super(Service, self).__init__()

    @property
    def is_running(self):
        """Test if service is running"""
        raise NotImplementedError

    @property
    def is_enabled(self):
        """Test if service is enabled"""
        raise NotImplementedError

    @classmethod
    def get_module_class(cls, host):

        classes = [
            LinuxServiceProvider,
            BSDServiceProvider,
            DarwinServiceProvider,
        ]

        in_service_providers = [Klass.provider(host) for Klass in classes]

        provider = [provider for provider in in_service_providers if provider is not None]
        if provider:
            return provider[0]

        raise NotImplementedError


    def __repr__(self):
        return "<service %s>" % (self.name,)


class SysvService(Service):

    @property
    def is_running(self):
        # based on /lib/lsb/init-functions
        # 0: program running
        # 1: program is dead and pid file exists
        # 3: not running and pid file does not exists
        # 4: Unable to determine status
        return self.run_expect(
            [0, 1, 3], "service %s status", self.name).rc == 0

    @property
    def is_enabled(self):
        return bool(self.check_output(
            "find /etc/rc?.d/ -name %s",
            "S??" + self.name,
        ))


class SystemdService(SysvService):

    @property
    def is_running(self):
        return self.run_expect(
            [0, 3], "systemctl is-active %s", self.name).rc == 0

    @property
    def is_enabled(self):
        cmd = self.run_test("systemctl is-enabled %s", self.name)
        if cmd.rc == 0:
            return True
        elif cmd.stdout.strip() == "disabled":
            return False
        # Fallback on SysV
        # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=760616
        return super(SystemdService, self).is_enabled


class UpstartService(SysvService):

    @property
    def is_enabled(self):
        if self.run(
            "grep -q '^start on' /etc/init/%s.conf",
            self.name,
        ).rc == 0 and self.run(
            "grep -q '^manual' /etc/init/%s.override",
            self.name,
        ).rc != 0:
            return True
        # Fallback on SysV
        return super(UpstartService, self).is_enabled

    @property
    def is_running(self):
        cmd = self.run_test('status %s', self.name)
        if cmd.rc == 0 and len(cmd.stdout.split()) > 1:
            return 'running' in cmd.stdout.split()[1]
        return super(UpstartService, self).is_running


class FreeBSDService(Service):

    @property
    def is_running(self):
        return self.run_test("service %s onestatus", self.name).rc == 0

    @property
    def is_enabled(self):
        # Return list of enabled services like
        # /etc/rc.d/sshd
        # /etc/rc.d/sendmail
        for path in self.check_output("service -e").splitlines():
            if path and path.rsplit("/", 1)[1] == self.name:
                return True
        return False


class OpenBSDService(Service):

    @property
    def is_running(self):
        return self.run_test("/etc/rc.d/%s check", self.name).rc == 0

    @property
    def is_enabled(self):
        raise NotImplementedError


class NetBSDService(Service):

    @property
    def is_running(self):
        return self.run_test("/etc/rc.d/%s onestatus", self.name).rc == 0

    @property
    def is_enabled(self):
        raise NotImplementedError


class LaunchdService(Service):

    @property
    def is_running(self):
        cmd = self.run_test("sudo /bin/launchctl list | grep '%s' | grep '^[-0-9]'", self.name)

        if cmd.rc == 0:
            # (Pdb) cmd.stdout
            # u'2034\t0\tcom.openssh.sshd.E8FE00AD-3911-4162-9D6E-6E2B82EDB7A9\n-\t0\tcom.openssh.sshd\n2133\t0\tcom.openssh.sshd.005AE32E-10CA-4368-AFEC-F85A09226D9B\n'
            # result will be [ [pid, status, label], [pid, status, label], ... ]
            return [re.split(r'[\t ]', line) for line in str(cmd.stdout).split('\n')]

    @property
    def is_enabled(self):
        raise NotImplementedError
