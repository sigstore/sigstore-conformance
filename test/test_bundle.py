from pathlib import Path
from test.client import BundleMaterials, SigstoreClient
from test.conftest import _MakeMaterialsByType

import pytest  # type: ignore
from cryptography import x509
from sigstore_protobuf_specs.dev.sigstore.bundle.v1 import Bundle


def test_verify(client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType) -> None:
    """
    Test the happy path of verification
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.good.sigstore")

    client.verify(materials, input_path)


def test_verify_dsse_bundle_with_trust_root(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Test the happy path of verification for DSSE bundle w/ custom trust root
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.good.sigstore")
    materials.trusted_root = Path("trusted_root.d.json")

    client.verify(materials, input_path)


def test_verify_rejects_root(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle that contains a root certificate.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("has_root_in_chain.txt", BundleMaterials)

    with client.raises():
        client.verify(materials, input_path)


@pytest.mark.signing
def test_sign_does_not_produce_root(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client does not produce a bundle that contains a root
    certificate.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    assert not materials.exists()

    # Sign for our input.
    client.sign(materials, input_path)

    # Parse the output bundle.
    bundle_contents = materials.bundle.read_bytes()
    bundle = Bundle().from_json(bundle_contents)

    # Iterate over our cert chain and check for roots.
    certs = bundle.verification_material.x509_certificate_chain
    for cert in certs.certificates:
        cert = x509.load_der_x509_certificate(cert.raw_bytes)

        try:
            constraints = cert.extensions.get_extension_for_class(x509.BasicConstraints)
            assert not constraints.value.ca
        # BasicConstraints isn't required to appear in leaf certificates.
        except x509.ExtensionNotFound:
            pass


def test_verify_rejects_staging_cert(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle that doesn't match trust root.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.staging.sigstore")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_invalid_set(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle with a signed entry timestamp from
    the future.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.invalid_set.sigstore")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_invalid_signature(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle with a modified signature.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.invalid_signature.sigstore")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_invalid_key(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle with a modified public key in the
    hashrekord entry.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.invalid_key.sigstore")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_invalid_inclusion_proof(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle with an old inclusion proof
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.invalid_inclusion_proof.sigstore")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_different_materials(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle for different materials.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("b.txt", BundleMaterials)
    materials.bundle = Path("a.txt.good.sigstore")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_expired_certificate(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle if the certificate was issued
    outside the validity window of the trusted root
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.cert-expired.sigstore")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_missing_inclusion_proof(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a v0.2 bundle if the TLog entry does NOT
    contain an inclusion proof
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.no-inclusion-proof.sigstore")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_bad_tlog_timestamp(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle if the TLog entry contains a
    timestamp that falls outside the validity window of the signing
    certificate.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.tlog-timestamp-error.sigstore")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_bad_tlog_entry(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle if the body of the TLog entry does
    not match the signed artifact.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.tlog-body-error.sigstore")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        client.verify(materials, input_path)


def test_verify_rejects_bad_tsa_timestamp(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle if the TSA timestamp falls outside
    the validity window of the signing certificate.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.tsa-timestamp-error.sigstore")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        client.verify(materials, input_path)
