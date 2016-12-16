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

from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from testinfra.modules.base import Module


class Record(object):
    """Record object collecting certificate name info"""
    def __init__(self):
        self.CN = None
        self.O = None
        self.OU = None
        self.C = None
        self.ST = None
        self.L = None

class Certificate(Module):
    """Test X509 public certificate attributes"""

    # File module to be loaded
    File = None

    def __init__(self, path, fmt="PEM"):
        super(Certificate, self).__init__()
        self._path = path
        self._fmt = fmt
        self._file = None
        self._cert = None
        self._load_certificate()

    @classmethod
    def get_module_class(cls, _backend):
        cls.File = _backend.get_module("File")
        return cls

    def _load_certificate(self):
        """Lazy certificate loading"""
        if self._file is None:
            self._file = self.File(self._path)
            contents = str(self._file.content_string)
            if self._fmt == "PEM":
                self._cert = x509.load_pem_x509_certificate(contents,
                                                            default_backend())
            elif self._fmt == "DER":
                self._cert = x509.load_der_x509_certificate(contents,
                                                            default_backend())
            else:
                RuntimeError("Invalid certificate format: %s" % self._fmt)
            # Fill in issuer and subject records
            nis = self._cert.issuer
            self._issuer = Record()
            self._issuer.C = nis.get_attributes_for_oid(
                NameOID.COUNTRY_NAME)[0].value
            self._issuer.O = nis.get_attributes_for_oid(
                NameOID.ORGANIZATION_NAME)[0].value
            self._issuer.CN = nis.get_attributes_for_oid(
                NameOID.COMMON_NAME)[0].value
            osb = self._cert.subject
            self._subject = Record()
            self._subject.C = osb.get_attributes_for_oid(
                NameOID.COUNTRY_NAME)[0].value
            self._subject.O = osb.get_attributes_for_oid(
                NameOID.ORGANIZATION_NAME)[0].value
            self._subject.OU = osb.get_attributes_for_oid(
                NameOID.ORGANIZATION_NAME)[0].value
            self._subject.CN = osb.get_attributes_for_oid(
                NameOID.COMMON_NAME)[0].value
            self._subject.ST = osb.get_attributes_for_oid(
                NameOID.STATE_OR_PROVINCE_NAME)[0].value
            self._subject.L = osb.get_attributes_for_oid(
                NameOID.LOCALITY_NAME)[0].value

    def __repr__(self):
        return "<certificate %s>" % (self._path,)

    @property
    def file(self):
        """Return the underlying testinfra File object

        You can perform further related file tests to the underlying file.
        >>> Certificate("/etc/pki/tls/certs/server.pem").file.user
        'root'
        """
        return self._file

    @property
    def has_expired(self):
        """Return True if certificate has expired

        >>> Certificate("/etc/pki/tls/certs/server.pem").has_expired
        False
        """
        return self._cert.not_valid_after < datetime.datetime.utcnow()

    @property
    def expiration_date(self):
        """Return certificate expiration date as a naive datetime object

        >>> Certificate("/etc/pki/tls/certs/server.pem").expiration_date
        datetime(.datetime(2017, 05, 27, 23, 59, 59)
        """
        return self._cert.not_valid_after

    @property
    def start_date(self):
        """Return certificate valid start date as a naive datetime object

        >>> Certificate("/etc/pki/tls/certs/server.pem").expiration_date
        datetime(.datetime(2016, 01, 3, 0, 0, 0)
        """
        return self._cert.not_valid_before

    @property
    def issuer(self):
        """Return the certificate issuer info as a Record object

        >>> Certificate("/etc/pki/tls/certs/server.pem").issuer.C
        'US'
        >>> Certificate("/etc/pki/tls/certs/server.pem").issuer.O
        'GeoTrust Unc.'
        >>> Certificate("/etc/pki/tls/certs/server.pem").issuer.CN
        'GeoTrust SSL CA - G3'
        """
        return self._issuer

    @property
    def subject(self):
        """Return the certificate subject info as a Record object

        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.C
        'ES'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.ST
        'MADRID'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.L
        'ALCORCON'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.O
        'ACME'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.CN
        'server.acme.com'
        >>> Certificate("/etc/pki/tls/certs/server.pem").subject.OU
        'ACME R&D'
        """
        return self._subject
