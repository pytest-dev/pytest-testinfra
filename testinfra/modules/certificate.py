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
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from testinfra.modules.base import Module

class Record(object):
    """Record object collecting certificate name info"""
    pass

class Certificate(Module):
    """Test X509 public certificate info"""

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
        """Return certificate UTC expiration date as a naive datetime object

        >>> Certificate("/etc/pki/tls/certs/server.pem").expiration_date
        datetime(.datetime(2017, 05, 27, 23, 59, 59)
        """
        return self._cert.not_valid_after


    @property
    def start_date(self):
        """Return certificate UTC valid start date as a naive datetime object

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
        oiss = self._cert.issuer
        niss = Record()
        niss.C = oiss.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value
        niss.O = oiss.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
        niss.CN = oiss.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        return niss

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
        osbj = self._cert.subject
        nsbj = Record()
        nsbj.C = osbj.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value
        nsbj.O = osbj.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
        nsbj.OU = osbj.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
        nsbj.CN = osbj.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        nsbj.ST = osbj.get_attributes_for_oid(NameOID.STATE_OR_PROVINCE_NAME)[0].value
        nsbj.L = oobj.get_attributes_for_oid(NameOID.LOCALITY_NAME)[0].value
        return nsbj
