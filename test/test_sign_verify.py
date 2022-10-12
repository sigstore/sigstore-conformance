from pathlib import Path

from .client import SigstoreClient


def test_sign_verify(client: SigstoreClient, workspace: Path) -> None:
    """
    A basic test that signs and verifies an artifact for a given sigstore client.
    """
    # Sign and verify the README
    client.sign("artifact.txt", "artifact.txt.crt", "artifact.txt.sig")
    client.verify("artifact.txt", "artifact.txt.crt", "artifact.txt.sig")
