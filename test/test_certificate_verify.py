from pathlib import Path

import pytest  # type: ignore

from .client import ClientFail, SignatureCertificateMaterials, SigstoreClient


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

    with pytest.raises(ClientFail):
        client.verify(materials, artifact_path)
