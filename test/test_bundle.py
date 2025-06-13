import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest  # type: ignore
from cryptography import x509
from sigstore_protobuf_specs.dev.sigstore.bundle.v1 import Bundle

from test.client import BundleMaterials, ClientFail, SigstoreClient
from test.conftest import _MakeMaterialsByType, _VerifyBundle

SKIP_CPYTHON_RELEASE_TESTS = (
    os.getenv("GHA_SIGSTORE_CONFORMANCE_SKIP_CPYTHON_RELEASE_TESTS", "false") != "false"
)

GITHUB_WORKSPACE = os.getenv("GITHUB_WORKSPACE")


def test_verify_bundle(
    client: SigstoreClient,
    subtests,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Test all bundles in assets/bundle-verify/*
    """

    for f in Path("bundle-verify").glob("*"):
        subtest_dir = Path(f)
        if not subtest_dir.is_dir():
            continue

        with subtests.test(subtest_dir.name):
            materials = BundleMaterials.from_path(subtest_dir / "bundle.sigstore.json")

            # use custom trust root if one is provided
            trusted_root_path = subtest_dir / "trusted_root.json"
            if trusted_root_path.exists():
                materials.trusted_root = trusted_root_path

            # use custom artifact path if one is provided
            artifact_path = subtest_dir / "artifact"
            if not artifact_path.exists():
                artifact_path = Path("bundle-verify", "a.txt")

            if subtest_dir.name.endswith("fail"):
                with client.raises():
                    verify_bundle(materials, artifact_path)
            else:
                verify_bundle(materials, artifact_path)


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
    bundle = Bundle.from_dict(json.loads(bundle_contents))

    # Iterate over our cert chain and check for roots.
    if bundle.verification_material.is_set("x509_certificate_chain"):
        certs = bundle.verification_material.x509_certificate_chain.certificates
    elif bundle.verification_material.is_set("certificate"):
        certs = [bundle.verification_material.certificate]
    else:
        assert False, "expected certs in either `x509_certificate_chain` or `certificate`"

    for x509cert in certs:
        cert = x509.load_der_x509_certificate(x509cert.raw_bytes)

        try:
            constraints = cert.extensions.get_extension_for_class(x509.BasicConstraints)
            assert not constraints.value.ca
        # BasicConstraints isn't required to appear in leaf certificates.
        except x509.ExtensionNotFound:
            pass


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


def test_verify_invalid_trust_root_ct_key(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Check that the client rejects a bundle if the trusted root CT key is wrong.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path("a.txt.good.sigstore.json")
    materials.trusted_root = Path("trusted_root.a.invalid_ct.json")

    with client.raises():
        verify_bundle(materials, input_path)


@pytest.mark.skipif(
    SKIP_CPYTHON_RELEASE_TESTS, reason="CPython release bundle tests explicitly skipped"
)
@pytest.mark.skipif(not GITHUB_WORKSPACE, reason="GITHUB_WORKSPACE not set")
def test_verify_cpython_release_bundles(subtests, client):
    cpython_release_dir = Path(GITHUB_WORKSPACE) / "cpython-release-tracker"
    if not cpython_release_dir.is_dir():
        pytest.skip("cpython-release-tracker data is not available")

    identities = json.loads((cpython_release_dir / "signing-identities.json").read_text())

    def version_path_to_identity(path: Path) -> dict[str, Any] | None:
        # Transforms /foo/bar/versions/3.11.6.json into a suitable
        # verification identity.

        # "3.11.6"
        full_version = path.with_suffix("").name

        # "3.11"
        version = ".".join(full_version.split(".")[0:2])

        return next((ident for ident in identities if ident["Release"] == version), None)

    def temp_bundle_path(bundle: dict) -> Path:
        # We let the system dispose of these after process teardown.
        tmpfile = tempfile.NamedTemporaryFile(mode="w+t", suffix=".sigstore.json", delete=False)
        tmpfile.write(json.dumps(bundle))
        tmpfile.close()

        return Path(tmpfile.name)

    versions = cpython_release_dir / "versions"
    for version_path in versions.glob("*.json"):
        ident = version_path_to_identity(version_path)
        if not ident:
            continue

        version = json.loads(version_path.read_text())
        for artifact in version:
            bundle = artifact.get("sigstore")
            if not bundle:
                continue
            with subtests.test(artifact["url"]):
                bundle_path = temp_bundle_path(bundle)
                sha256 = artifact["sha256"]

                # NOTE: We currently do this completely manually,
                # since the client verify APIs are baked around
                # the assumption of a static identity.
                try:
                    client.run(
                        "verify-bundle",
                        "--bundle",
                        str(bundle_path),
                        "--certificate-identity",
                        ident["Release manager"],
                        "--certificate-oidc-issuer",
                        ident["OIDC Issuer"],
                        f"sha256:{sha256}",
                    )
                except ClientFail as e:
                    pytest.fail(f"verify for {artifact['url']} failed: {e}")

                # One verification per release is enough
                break


@pytest.mark.parametrize("test_file_ext", ["bad_sig", "mismatched_sig", "mismatched_envelope"])
def test_verify_in_toto_in_dsse_envelope_rejects_invalid_envelope(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    verify_bundle: _VerifyBundle,
    test_file_ext: str,
) -> None:
    """
    Check that the client will fail if the dsse envelope is invalid or inconsistent with the bundle
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.bundle = Path(f"intoto-in-dsse-v3.{test_file_ext}.sigstore.json")

    with client.raises():
        verify_bundle(materials, input_path)
