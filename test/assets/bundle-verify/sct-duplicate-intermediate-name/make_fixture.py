#!/usr/bin/env python3
"""Generate the trusted_root.json for the `sct-duplicate-intermediate-name` test.

Regression fixture for the SCT-verification bug fixed in sigstore-rust #154.

Scenario
--------
Fulcio's SCT is verified against `issuer_key_hash = SHA-256(issuer SPKI)`
(RFC 6962 precert entry). A client must resolve *which* intermediate issued the
leaf and hash *that* key. A client that resolves the issuer by Subject **name
only** breaks the moment the trust root holds two intermediates with the same
Subject DN but different keys (a real event: Fulcio staging rolled a second,
identically-named intermediate during the multi-region migration in July 2026).
The name-only matcher may select the wrong SPKI, so the SCT signature check
fails even though the bundle is perfectly valid.

This fixture reproduces that shape deterministically: it takes the real
public-good production trust root (which verifies the `happy-path` bundle) and
injects a **decoy** certificate authority whose intermediate shares the genuine
intermediate's Subject DN (`CN=sigstore-intermediate,O=sigstore.dev`) but has a
different key. A correct client sources the issuer key from the cryptographically
verified certificate chain and still verifies the SCT; a name-only matcher picks
the decoy and fails.

The bundle itself is unchanged `happy-path` material (beacon identity), so it
passes the suite's fixed identity/issuer policy unchanged — the *only* variable
under test is issuer resolution for SCT.

Usage
-----
    python make_fixture.py \
        --base ../../../../crates/sigstore-trust-root/src/trusted_root.json \
        --out trusted_root.json

`--base` must point at the production public-good trusted root that verifies the
happy-path bundle. The path above is relative to this fixture directory when the
sigstore-rust checkout sits alongside the conformance checkout; adjust as needed.
"""
from __future__ import annotations

import argparse
import base64
import copy
import datetime
import json
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

# Subject DN shared by the genuine public-good intermediate and the decoy.
#
# The DN must byte-for-byte match the genuine intermediate's Subject, because a
# name-only issuer resolver compares the encoded DN structurally. The genuine
# Fulcio intermediate encodes its attributes as PrintableString (ASN.1 tag
# 0x13); `cryptography` defaults to UTF8String (0x0c). Force PrintableString so
# the collision actually occurs — otherwise the resolver skips the decoy and the
# fixture silently fails to reproduce the bug.
INTERMEDIATE_NAME = x509.Name(
    [
        x509.NameAttribute(
            NameOID.ORGANIZATION_NAME,
            "sigstore.dev",
            _type=x509.name._ASN1Type.PrintableString,
        ),
        x509.NameAttribute(
            NameOID.COMMON_NAME,
            "sigstore-intermediate",
            _type=x509.name._ASN1Type.PrintableString,
        ),
    ]
)


def build_decoy_cert() -> x509.Certificate:
    """A self-signed CA cert with the genuine intermediate's Subject DN but a
    fresh, unrelated key. Self-signed so it is internally consistent as a CA
    entry (it is its own root), which keeps spec-compliant clients from
    rejecting the trust root outright."""
    key = ec.generate_private_key(ec.SECP256R1())
    # Deterministic, clearly-not-real validity window that brackets the
    # happy-path signing time (2023-07-12) with a wide margin so a name+time
    # matcher still considers the decoy a candidate.
    not_before = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    not_after = datetime.datetime(2035, 1, 1, tzinfo=datetime.timezone.utc)
    ski = x509.SubjectKeyIdentifier.from_public_key(key.public_key())
    return (
        x509.CertificateBuilder()
        .subject_name(INTERMEDIATE_NAME)
        .issuer_name(INTERMEDIATE_NAME)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(ski, critical=False)
        .sign(key, hashes.SHA256())
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True, type=Path, help="production trusted_root.json")
    ap.add_argument("--out", required=True, type=Path, help="fixture trusted_root.json to write")
    args = ap.parse_args()

    tr = json.loads(args.base.read_text())

    decoy = build_decoy_cert()
    decoy_der = decoy.public_bytes(serialization.Encoding.DER)
    decoy_b64 = base64.b64encode(decoy_der).decode()

    # Model the decoy as its own certificateAuthorities entry, mirroring the
    # shape of the genuine `sigstore-intermediate` CA. Inserted BEFORE the
    # genuine CA so a naive "first Subject-name match wins" resolver selects the
    # decoy.
    decoy_ca = {
        "subject": {"organization": "sigstore.dev", "commonName": "sigstore-intermediate"},
        "uri": "https://fulcio.example.invalid",
        "certChain": {"certificates": [{"rawBytes": decoy_b64}]},
        "validFor": {"start": "2020-01-01T00:00:00Z"},
    }

    cas = tr.get("certificateAuthorities", [])
    # Find the genuine intermediate CA (the one whose chain contains a cert with
    # the shared Subject DN) and insert the decoy just before it.
    insert_at = 0
    for i, ca in enumerate(cas):
        for c in ca.get("certChain", {}).get("certificates", []):
            cert = x509.load_der_x509_certificate(base64.b64decode(c["rawBytes"]))
            if cert.subject == INTERMEDIATE_NAME:
                insert_at = i
                break
        else:
            continue
        break
    cas.insert(insert_at, decoy_ca)
    tr["certificateAuthorities"] = cas

    args.out.write_text(json.dumps(tr, indent=2) + "\n")
    print(f"wrote {args.out} with decoy intermediate inserted at index {insert_at}")


if __name__ == "__main__":
    main()
