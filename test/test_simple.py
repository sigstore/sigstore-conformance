from pathlib import Path

from .client import SigstoreClient


def test_simple(client: SigstoreClient) -> None:
    """
    A simple test that signs and verifies an artifact for a given Sigstore
    client.
    """
    artifact_path = Path("a.txt")
    certificate_path = Path("a.txt.crt")
    signature_path = Path("a.txt.sig")

    assert artifact_path.exists()
    assert not certificate_path.exists()
    assert not signature_path.exists()

    # Sign the artifact.
    client.sign(artifact_path, certificate_path, signature_path)

    assert certificate_path.exists()
    assert signature_path.exists()

    # Verify the artifact signature.
    client.verify(artifact_path, certificate_path, signature_path)
