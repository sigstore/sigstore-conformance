from pathlib import Path

from .client import SigstoreClient


def test_sign_verify(client: SigstoreClient) -> None:
    """
    A basic test that signs and verifies an artifact for a given Sigstore
    client.
    """
    artifact_path = Path("artifact.txt")
    signature_path = Path("artifact.txt.sig")
    certificate_path = Path("artifact.txt.crt")

    assert artifact_path.exists()
    assert not signature_path.exists()
    assert not certificate_path.exists()

    # Sign the artifact.
    client.sign(artifact_path, signature_path, certificate_path)

    assert signature_path.exists()
    assert certificate_path.exists()

    with certificate_path.open() as f:
        print(f.read())

    # Verify the artifact signature.
    client.verify(artifact_path, signature_path, certificate_path)
