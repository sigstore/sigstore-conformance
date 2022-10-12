from pathlib import Path

from .client import SigstoreClient


def test_sign_verify(client: SigstoreClient, workspace: Path) -> None:
    """
    A basic test that signs and verifies an artifact for a given Sigstore
    client.
    """
    # Sign and verify the artifact.
    client.sign(
        Path("artifact.txt"), Path("artifact.txt.crt"), Path("artifact.txt.sig")
    )
    client.verify(
        Path("artifact.txt"), Path("artifact.txt.crt"), Path("artifact.txt.sig")
    )
