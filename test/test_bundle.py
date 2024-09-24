from pathlib import Path

import pytest  # type: ignore
from cryptography import x509
from sigstore_protobuf_specs.dev.sigstore.bundle.v1 import Bundle

from test.client import BundleMaterials, SigstoreClient
from test.conftest import _MakeMaterialsByType, _VerifyBundle


def test_verify(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Test the happy path of verification
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.good.sigstore.json")

    verify_bundle(materials, input_path)


def test_verify_v_0_3(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Test the happy path of verification of a v0.3 bundle
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.good.v0.3.sigstore")

    verify_bundle(materials, input_path)


def test_verify_dsse_bundle_with_trust_root(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Test the happy path of verification for DSSE bundle w/ custom trust root
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.good.sigstore.json")
    materials.trusted_root = Path("trusted_root.d.json")

    verify_bundle(materials, input_path)


def test_verify_rejects_root(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle that contains a root certificate.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("has_root_in_chain.txt", BundleMaterials)

    with client.raises():
        verify_bundle(materials, input_path)


@pytest.mark.signing
def test_sign_does_not_produce_root(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
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
    for x509cert in certs.certificates:
        cert = x509.load_der_x509_certificate(x509cert.raw_bytes)

        try:
            constraints = cert.extensions.get_extension_for_class(x509.BasicConstraints)
            assert not constraints.value.ca
        # BasicConstraints isn't required to appear in leaf certificates.
        except x509.ExtensionNotFound:
            pass


def test_verify_rejects_staging_cert(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle that doesn't match trust root.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.staging.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_invalid_set(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle with a signed entry timestamp from
    the future.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.invalid_set.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_invalid_signature(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle with a modified signature.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.invalid_signature.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_invalid_key(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle with a modified public key in the
    hashrekord entry.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.invalid_key.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_invalid_inclusion_proof(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle with an old inclusion proof
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.invalid_inclusion_proof.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_different_materials(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle for different materials.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("b.txt", BundleMaterials)
    materials.bundle = Path("a.txt.good.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_expired_certificate(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle if the certificate was issued
    outside the validity window of the trusted root
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.cert-expired.sigstore.json")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_missing_inclusion_proof(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a v0.2 bundle if the TLog entry does NOT
    contain an inclusion proof
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.no-inclusion-proof.sigstore.json")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_bad_tlog_timestamp(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle if the TLog entry contains a
    timestamp that falls outside the validity window of the signing
    certificate.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.tlog-timestamp-error.sigstore.json")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_bad_tlog_entry(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle if the body of the TLog entry does
    not match the signed artifact.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.tlog-body-error.sigstore.json")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_bad_tsa_timestamp(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle if the TSA timestamp falls outside
    the validity window of the signing certificate.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("d.txt", BundleMaterials)
    materials.bundle = Path("d.txt.tsa-timestamp-error.sigstore.json")
    materials.trusted_root = Path("trusted_root.d.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_bad_checkpoint(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle if the checkpoint signature is
    invalid.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.checkpoint_invalid_signature.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_valid_but_mismatched_checkpoint(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle if the checkpoint self consistent
    but does not apply to this bundle (root hash is wrong).
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.checkpoint_wrong_roothash.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)


def test_verify_rejects_checkpoint_with_no_matching_key(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle if the checkpoint signature
    does not match the transparency log providing the entry.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.checkpoint_bad_keyhint.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)
