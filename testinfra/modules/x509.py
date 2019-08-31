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

from dateutil import parser
from OpenSSL import crypto
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
        """Return serial of certificate

        >>> host.x509('/etc/pki/tls/certs/dummy.crt').serial
        """

        raise NotImplementedError

    def __repr__(self):
        return "<x509 %s>" % (self.name,)

    @classmethod
    def get_module_class(cls, host):
        return OpenSSL


class OpenSSL(X509):

    @property
    def issuer(self):
        return crypto.load_certificate(
            crypto.FILETYPE_PEM, open(self.name, 'r').read()
        ).get_issuer()

    @property
    def subject(self):
        return crypto.load_certificate(
            crypto.FILETYPE_PEM, open(self.name, 'r').read()
        ).get_subject()

    @property
    def enddate(self):
        return parser.parse(crypto.load_certificate(
            crypto.FILETYPE_PEM, open(self.name, 'r').read()
        ).get_notAfter())

    @property
    def serial(self):
        return crypto.load_certificate(
            crypto.FILETYPE_PEM, open(self.name, 'r').read()
        ).get_serial_number()
