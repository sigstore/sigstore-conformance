from pathlib import Path
from test.conftest import _MakeMaterials, _MakeMaterialsByType

import pytest  # type: ignore

from .client import SignatureCertificateMaterials, SigstoreClient


@pytest.mark.signing
@pytest.mark.staging
def test_verify_empty(client: SigstoreClient, make_materials: _MakeMaterials) -> None:
    """
    Tests that verification fails with empty artifacts, certificates and
    signatures.
    """
    artifact_path, materials = make_materials("a.txt")

    assert artifact_path.exists()
    assert not materials.exists()

    # Sign the artifact.
    client.sign(materials, artifact_path)
    assert materials.exists()

    # Write a blank temporary file.
    blank_path = Path("blank.txt")
    blank_path.touch()

    # Verify with an empty artifact.
    with client.raises():
        client.verify(materials, blank_path)

    # Verify with correct inputs.
    client.verify(materials, artifact_path)


@pytest.mark.signing
@pytest.mark.staging
def test_verify_mismatch(client: SigstoreClient, make_materials: _MakeMaterials) -> None:
    """
    Tests that verification fails with mismatching artifacts, certificates and
    signatures.
    """
    a_artifact_path, a_materials = make_materials("a.txt")

    assert a_artifact_path.exists()
    assert not a_materials.exists()

    # Sign a.txt.
    client.sign(a_materials, a_artifact_path)
    assert a_materials.exists()

    # Sign b.txt.
    b_artifact_path, b_materials = make_materials("b.txt")

    client.sign(b_materials, b_artifact_path)
    assert b_materials.exists()

    # Verify with a mismatching artifact.
    with client.raises():
        client.verify(a_materials, b_artifact_path)

    # Verify with correct inputs.
    client.verify(a_materials, a_artifact_path)


@pytest.mark.signing
def test_verify_sigcrt(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Test cases for the signature+certificate flow: empty sigs/crts and
    mismatched sigs/crts.
    """
    a_artifact_path, a_materials = make_materials_by_type("a.txt", SignatureCertificateMaterials)
    b_artifact_path, b_materials = make_materials_by_type("b.txt", SignatureCertificateMaterials)

    # Sign a.txt, b.txt.
    client.sign(a_materials, a_artifact_path)
    client.sign(b_materials, b_artifact_path)

    # Write a blank temporary file.
    blank_path = Path("blank.txt")
    blank_path.touch()

    # Verify with an empty signature.
    with client.raises():
        blank_sig = SignatureCertificateMaterials()
        blank_sig.signature = blank_path
        blank_sig.certificate = a_materials.certificate

        client.verify(blank_sig, a_artifact_path)

    # Verify with an empty certificate.
    with client.raises():
        blank_crt = SignatureCertificateMaterials()
        blank_crt.signature = a_materials.signature
        blank_crt.certificate = blank_path

        client.verify(blank_crt, a_artifact_path)

    # Verify with a mismatching certificate.
    with client.raises():
        crt_mismatch = SignatureCertificateMaterials()
        crt_mismatch.certificate = b_materials.certificate
        crt_mismatch.signature = a_materials.signature

        client.verify(crt_mismatch, a_artifact_path)

    # Verify with a mismatching signature.
    with client.raises():
        sig_mismatch = SignatureCertificateMaterials()
        sig_mismatch.certificate = a_materials.certificate
        sig_mismatch.signature = b_materials.signature

        client.verify(sig_mismatch, a_artifact_path)

    # Verify with correct inputs.
    client.verify(a_materials, a_artifact_path)
