#!/usr/bin/env python

import datetime
from pathlib import Path
from sys import argv

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID
from sigstore._internal.tuf import TrustUpdater
from sigstore.oidc import Issuer
from sigstore.sign import Signer
from sigstore_protobuf_specs.dev.sigstore.common.v1 import X509Certificate

if len(argv) < 2:
    print(f"usage: {argv[0]} [data directory]")
    exit(-1)


_DATA_DIRECTORY = Path(argv[1])
assert _DATA_DIRECTORY.exists() and _DATA_DIRECTORY.is_dir

_SIGNER = Signer.staging()
_ISSUER = Issuer.staging()
_TOKEN = _ISSUER.identity_token()


def _keypair():
    priv = ec.generate_private_key(ec.SECP384R1())
    return priv.public_key(), priv


_ROOT_PUBKEY, _ROOT_PRIVKEY = _keypair()

_A_VERY_LONG_TIME = datetime.timedelta(days=365 * 1000)


def _builder() -> x509.CertificateBuilder:
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(
        x509.Name(
            [
                x509.NameAttribute(
                    NameOID.COMMON_NAME, "sigstore-conformance-bogus-cert"
                ),
            ]
        )
    )
    builder = builder.issuer_name(
        x509.Name(
            [
                x509.NameAttribute(
                    NameOID.COMMON_NAME, "sigstore-conformance-bogus-cert"
                ),
            ]
        )
    )
    builder = builder.not_valid_before(datetime.datetime.today())
    builder = builder.not_valid_after(datetime.datetime.today() + _A_VERY_LONG_TIME)
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.add_extension(
        x509.SubjectAlternativeName([x509.DNSName("bogus.example.com")]), critical=False
    )
    return builder


def _finalize(
    builder: x509.CertificateBuilder, *, pubkey=_ROOT_PUBKEY, privkey=_ROOT_PRIVKEY
) -> x509.Certificate:
    builder = builder.public_key(pubkey)
    return builder.sign(private_key=privkey, algorithm=hashes.SHA256())


def _build_has_root_in_chain():
    input = _DATA_DIRECTORY / "has_root_in_chain.txt"
    assert input.exists()

    result = _SIGNER.sign(input.open("rb"), _TOKEN)
    bundle = result._to_bundle()

    # XX: this may return certificates for more than one path, which should still
    # be fine for our use case. We just need at least one root certificate in the
    # bundle chain.
    chain_certs = TrustUpdater.staging().get_fulcio_certs()
    bundle_chain = bundle.verification_material.x509_certificate_chain
    bundle_chain.certificates.extend(
        [
            X509Certificate(raw_bytes=cert.public_bytes(encoding=Encoding.DER))
            for cert in chain_certs
        ]
    )

    output = _DATA_DIRECTORY / "has_root_in_chain.txt.sigstore"
    print(bundle.to_json(), file=output.open("w"))


def _build_missing_ski_aki():
    input = _DATA_DIRECTORY / "missing_ski_aki.txt"
    assert input.exists()

    result = _SIGNER.sign(input.open("rb"), _TOKEN)
    bundle = result._to_bundle()

    # Add a new certificate that does not include SKI or AKI extensions.
    bundle_chain = bundle.verification_material.x509_certificate_chain
    bad_cert = _finalize(_builder())

    bundle_chain.certificates.append(
        X509Certificate(raw_bytes=bad_cert.public_bytes(Encoding.DER))
    )

    output = _DATA_DIRECTORY / "missing_ski_aki.txt.sigstore"
    print(bundle.to_json(), file=output.open("w"))


_build_has_root_in_chain()
_build_missing_ski_aki()
