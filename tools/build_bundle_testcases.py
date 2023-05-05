#!/usr/bin/env python

from pathlib import Path
from sys import argv

from cryptography.hazmat.primitives.serialization import Encoding
from sigstore._internal.tuf import TrustUpdater
from sigstore.oidc import Issuer
from sigstore.sign import Signer
from sigstore_protobuf_specs.dev.sigstore.common.v1 import X509Certificate

if len(argv) < 2:
    print(f"usage: {argv[0]} [data directory]")
    exit(-1)

_DATA_DIRECTORY = Path(argv[1])
assert _DATA_DIRECTORY.exists() and _DATA_DIRECTORY.is_dir

_SIGNER = Signer.production()
_ISSUER = Issuer.production()
_TOKEN = _ISSUER.identity_token()


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


_build_has_root_in_chain()
