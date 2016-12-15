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

import datetime

from OpenSSL import crypto
from testinfra.modules.base import Module


class Certificate(Module):
    """Test X509 public certificate info"""

    # File module to be loaded
    File = None

    def __init__(self, path, fmt=crypto.FILETYPE_PEM):
        super(Certificate, self).__init__()
        self._path = path
        self._fmt = fmt
        self._cert = None
        self._load_certificate()

    def _load_certificate(self):
        """Lazy certificate loading"""
        if self._cert is None:
          
            self._file = self.File(self._path)
            if self._fmt == crypto.FILETYPE_PEM:
                content = self._file.content_string
            else:
                content = self._file.content
            self._cert = crypto.load_certificate(self._fmt, content)

    @property
    def file(self):
        """Return the underlying testinfra File object

        You can perform further related file tests to the underlying file.
        >>> Certificate("/etc/pki/tls/certs/server.pem").file
        <file '/etc/pki/tls/certs/server.pem'>
        """
        return self._file

    @property
    def issuer(self):
        """Return the certificate issuer info as a X509Name object

        >>> Certificate("/etc/pki/tls/certs/server.pem").issuer
        <X509Name object '/C=US/O=GeoTrust Inc./CN=GeoTrust SSL CA - G3'>
        >>> Certificate("/etc/pki/tls/certs/server.pem").issuer.C
        'US'
        >>> Certificate("/etc/pki/tls/certs/server.pem").issuer.O
        'GeoTrust Unc.'
        >>> Certificate("/etc/pki/tls/certs/server.pem").issuer.CN
        'GeoTrust SSL CA - G3'
        """
        return self._cert.get_issuer()

    @property
    def subject(self):
        """Return the certificate subject info as a X509Name object

        >>> Certificate("/etc/pki/tls/certs/server.pem").subject
        <X509Name object '/C=ES/ST=MADRID/L=MADRID/O=Telefonica Investigacion y Desarrollo SA/OU=IoT Platform/CN=*.iotplatform.telefonica.com'>
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.C
        'ES'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.ST
        'MADRID'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.L
        'ALCORCON'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.O
        'ACME'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.OU
        'ACME R&D'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.CN
        'server.acme.com'
        """
        return self._cert.get_subject()

    @property
    def has_expired(self):
        """Return True if certificate has expired

        >>> Certificate("/etc/pki/tls/certs/server.pem").has_expired
        False
        """
        return self._cert.has_expired

    @property
    def expiration_date(self):
        """Return certificate UTC expiration date as a naive datetime object

        >>> Certificate("/etc/pki/tls/certs/server.pem").expiration_date
        datetime(.datetime(2017, 05, 27, 23, 59, 59)
        """
        return datetime.datetime.strptime(
            self._cert.get_notAfter(), "%Y%m%d%H%M%SZ")

    def __repr__(self):
        return "<certificate %s>" % (self._path,)

    @classmethod
    def get_module_class(cls, _backend):
        cls.File = _backend.get_module("File")
        return cls

