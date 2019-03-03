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

from datetime import datetime
from testinfra.utils import cached_property
from testinfra.modules.base import Module


class X509(Module):

    def __init__(self, name):
        self.name = name
        super(X509, self).__init__()

    @property
    def issuer(self):
        """Return issuer of certificate
        >>> host.x509('/etc/pki/tls/certs/dummy.crt').issuer
        """
        raise NotImplementedError

    @property
    def email(self):
        """Return email of certificate
        >>> host.x509('/etc/pki/tls/certs/dummy.crt').email
        """
        raise NotImplementedError

    @property
    def subject(self):
        """Return subject of certificate
        >>> host.x509('/etc/pki/tls/certs/dummy.crt').subject
        """
        raise NotImplementedError

    @property
    def enddate(self):
        """Return enddate as datetime of certificate
        >>> host.x509('/etc/pki/tls/certs/dummy.crt').enddate
        """
        raise NotImplementedError

    @property
    def serial(self):
        """Return enddate as datetime of certificate
        >>> host.x509('/etc/pki/tls/certs/dummy.crt').serial
        """
        raise NotImplementedError

    def __repr__(self):
        return "<x509 %s>" % (self.name,)

    @classmethod
    def get_module_class(cls, host):
        return OpenSSL


class OpenSSL(X509):

    @cached_property
    def _openssl(self):
        return self._find_command('openssl')

    @property
    def issuer(self):
        stdout = self.check_output(
            '%s x509 -in %s -noout -issuer', self._openssl, self.name
        )
        return stdout

    @property
    def subject(self):
        stdout = self.check_output(
            '%s x509 -in %s -noout -subject', self._openssl, self.name
        )
        return stdout

    @property
    def email(self):
        stdout = self.check_output(
            '%s x509 -in %s -noout -email', self._openssl, self.name
        )
        return stdout

    @property
    def enddate(self):
        enddate = self.check_output(
            '%s x509 -in %s -noout -enddate', self._openssl, self.name
        )
        ret = datetime.strptime(enddate.split('=')[1], '%b %d %H:%M:%S %Y %Z')
        return ret

    @property
    def serial(self):
        serial = self.check_output(
            '%s x509 -in %s -noout -serial', self._openssl, self.name
        )
        ret = serial.split('=')[1]
        return ret
