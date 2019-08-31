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

from OpenSSL import crypto
from testinfra.modules.base import Module


class X509(Module):

    def __init__(self, name):
        self.name = name
        self._cert = crypto.load_certificate(
            crypto.FILETYPE_PEM, self._host.file(self.name).content_string
        )
        super(X509, self).__init__()

    @property
    def issuer(self):
        """Return issuer of certificate

        >>> host.x509('/etc/pki/tls/certs/dummy.crt').issuer
        """

        return self._cert.get_issuer()

    @property
    def subject(self):
        """Return subject of certificate

        >>> host.x509('/etc/pki/tls/certs/dummy.crt').subject
        """

        return self._cert.get_subject()

    @property
    def enddate(self):
        """Return enddate as datetime of certificate

        >>> host.x509('/etc/pki/tls/certs/dummy.crt').enddate
        """

        return self._cert.get_notAfter()

    @property
    def serial(self):
        """Return serial of certificate

        >>> host.x509('/etc/pki/tls/certs/dummy.crt').serial
        """

        return self._cert.get_serial_number()

    def __repr__(self):
        return "<x509 %s>" % (self.name,)
