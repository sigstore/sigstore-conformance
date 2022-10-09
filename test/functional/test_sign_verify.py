from pathlib import Path

from ..container import Container


def test_sign_verify(client: Container, workspace: Path) -> None:
    """
    A basic test that signs and verifies this repository's README with a given
    sigstore client.
    """
    # Sign and verify the README
    client.sign(
        "--output-certificate artifact.txt.crt --output-signature artifact.txt.sig artifact.txt"
    )
    client.verify("--cert artifact.txt.crt --signature artifact.txt.sig artifact.txt")
