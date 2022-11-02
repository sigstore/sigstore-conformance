from pathlib import Path

from .client import SigstoreClient


def test_sign_verify(client: SigstoreClient) -> None:
    """
    A basic test that signs and verifies an artifact for a given Sigstore
    client.
    """
    artifact_path = Path("artifact.txt")
    certificate_path = Path("artifact.txt.crt")
    signature_path = Path("artifact.txt.sig")

    assert artifact_path.exists
    assert not certificate_path.exists
    assert not signature_path.exists

    # Sign and verify the artifact.
    client.sign(artifact_path, certificate_path, signature_path)

    assert certificate_path.exists
    assert signature_path.exists

    client.verify(artifact_path, certificate_path, signature_path)
