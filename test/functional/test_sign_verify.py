from pathlib import Path

from ..matrix import SigstoreClient


def test_sign_verify(client: SigstoreClient, workspace: Path) -> None:
    """
    A basic test that signs and verifies an artifact with a given sigstore client
    """
    # Sign and verify the README
    client.sign("artifact.txt", "artifact.txt.crt", "artifact.txt.sig")
    client.verify("artifact.txt", "artifact.txt.crt", "artifact.txt.sig")
