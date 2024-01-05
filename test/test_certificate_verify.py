from pathlib import Path

from .client import SignatureCertificateMaterials, SigstoreClient


def test_verify_invalid_certificate_chain(client: SigstoreClient) -> None:
    """
    Tests that even if the signature is valid for a given certificate and
    artifact, verification will fail if the certificate is not issued by the
    configured root CA.

    For this test, we're using a certificate issued by the staging Fulcio
    instance.
    """
    artifact_path = Path("a.txt")
    signature_path = Path("a.txt.invalid.sig")
    certificate_path = Path("a.txt.invalid.crt")
    materials = SignatureCertificateMaterials()

    materials.certificate = certificate_path
    materials.signature = signature_path

    with client.raises():
        client.verify(materials, artifact_path)


def test_verify_with_trust_root(client: SigstoreClient) -> None:
    """
    Test verifying with the correct trusted root
    """
    artifact_path = Path("a.txt")
    signature_path = Path("a.txt.good.sig")
    certificate_path = Path("a.txt.good.crt")
    trusted_root = Path("trusted_root.public_good.json")

    materials = SignatureCertificateMaterials()
    materials.certificate = certificate_path
    materials.signature = signature_path
    materials.trusted_root = trusted_root

    client.verify(materials, artifact_path)


def test_verify_trust_root_with_invalid_ct_keys(client: SigstoreClient) -> None:
    """
    Test verifying with a trusted root with an incorrect CT keys.

    The artifact was signed with production, but the trusted root has staging
    CT keys.
    """
    artifact_path = Path("a.txt")
    signature_path = Path("a.txt.good.sig")
    certificate_path = Path("a.txt.good.crt")
    trusted_root = Path("trusted_root.bad_ct.json")

    materials = SignatureCertificateMaterials()
    materials.certificate = certificate_path
    materials.signature = signature_path
    materials.trusted_root = trusted_root

    with client.raises():
        client.verify(materials, artifact_path)

def test_verify_valid_cert_chain_but_only_leaf_on_log(client: SigstoreClient) -> None:
    """
    Test verifying all certificate verification should pass, but a log entry
    could not be found because the provided chain is not on the log, only
    the leaf is.

    This is to ensure clients are checking the provided certificate chain to 
    do log entry lookups, not just the leaf
    """
    artifact_path = Path("a.txt")
    signature_path = Path("a.txt.good.sig")
    certificate_path = Path("a.txt.good.full_crt")

    materials = SignatureCertificateMaterials()
    materials.certificate = certificate_path
    materials.signature = signature_path

    with client.raises():
        client.verify(materials, artifact_path)
