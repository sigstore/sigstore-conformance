import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest  # type: ignore
from cryptography import x509
from sigstore_protobuf_specs.dev.sigstore.bundle.v1 import Bundle
from sigstore_protobuf_specs.dev.sigstore.rekor.v1 import KindVersion

from test.client import BundleMaterials, ClientFail, SigstoreClient
from test.conftest import _MakeMaterialsByType, _VerifyBundle

SKIP_CPYTHON_RELEASE_TESTS = (
    os.getenv("GHA_SIGSTORE_CONFORMANCE_SKIP_CPYTHON_RELEASE_TESTS", "false") != "false"
)

GITHUB_WORKSPACE = os.getenv("GITHUB_WORKSPACE")


def test_verify(
    client: SigstoreClient,
    bundle_verify_dir,
    verify_bundle: _VerifyBundle,
) -> None:
    """
    Test all bundles in assets/bundle-verify/*. See assets/bundle-verify/README
    """
    path = Path(bundle_verify_dir)

    materials = BundleMaterials.from_path(path / "bundle.sigstore.json")

    # use custom trust root if one is provided
    trusted_root_path = path / "trusted_root.json"
    if trusted_root_path.exists():
        materials.trusted_root = trusted_root_path

    # use managed key for verifying if one is provided
    key_path = path / "key.pub"
    if key_path.exists():
        materials.key = key_path

    # use custom artifact path if one is provided
    artifact_path = path / "artifact"
    if not artifact_path.exists():
        artifact_path = Path("bundle-verify", "a.txt")

    if path.name.endswith("fail"):
        with client.raises():
            verify_bundle(materials, artifact_path)
    else:
        verify_bundle(materials, artifact_path)


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

    # Ensure valid message signature and no DSSE envelope
    assert bundle.is_set("message_signature")
    assert not bundle.is_set("dsse_envelope")

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


@pytest.mark.signing
def test_sign_verify_rekor2(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    project_root: Path,
    staging_config: tuple[Path, Path],
) -> None:
    """
    assert that client can sign a rekor 2 bundle
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    assert not materials.exists()

    # use current staging signingconfig & trusted root
    materials.trusted_root, materials.signing_config = staging_config

    # Sign for our input.
    client.sign(materials, input_path)

    # Parse the output bundle, verify it really contains a rekor2 entry
    bundle = Bundle.from_dict(json.loads(materials.bundle.read_bytes()))
    kv = bundle.verification_material.tlog_entries[0].kind_version
    assert kv == KindVersion("hashedrekord", "0.0.2")

    # assert client itself verifies the bundle it produced
    client.verify(materials, input_path)

    # Use selftest client verify to assert that the bundle is correctly formed
    # (contains a valid TSA timestamp etc)
    selftest_client = SigstoreClient(
        str(project_root / "selftest-client"), client.identity_token, client.staging
    )
    selftest_client.verify(materials, input_path)


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


@pytest.mark.signing
def test_sign_verify_dsse(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    project_root: Path,
) -> None:
    """
    Check that the client can sign a bundle with a DSSE envelope.
    """
    materials: BundleMaterials
    input_path, materials = make_materials_by_type("statement.json", BundleMaterials)
    assert not materials.exists()

    # Sign for our input with DSSE enabled.
    client.sign(materials, input_path, dsse=True)

    # Parse the output bundle.
    bundle_contents = materials.bundle.read_bytes()
    bundle = Bundle.from_dict(json.loads(bundle_contents))

    # Ensure DSSE envelope is present and message signature is NOT present
    assert bundle.is_set("dsse_envelope")
    assert not bundle.is_set("message_signature")

    # Ensure DSSE envelope payload matches the statement
    assert bundle.dsse_envelope.payload == input_path.read_bytes()

    # Verify the bundle
    artifact_path = input_path.parent / "a.txt"
    client.verify(materials, artifact_path)

    # Use selftest client verify to assert that the bundle is correctly formed
    selftest_client = SigstoreClient(
        str(project_root / "selftest-client"), client.identity_token, client.staging
    )
    selftest_client.verify(materials, artifact_path)
