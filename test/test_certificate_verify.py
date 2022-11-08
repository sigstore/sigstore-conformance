import subprocess
from pathlib import Path

import pytest  # type: ignore

from .client import SigstoreClient


def test_verify_invalid_certificate_chain(client: SigstoreClient) -> None:
    """
    Tests that even if the signature is valid for a given certificate and
    artifact, verification will fail if the certificate is not issued by the
    configured root CA.

    For this test, we're using a certificate issued by the staging Fulcio
    instance.
    """
    artifact_path = Path("a.txt")
    certificate_path = Path("a.txt.invalid.crt")
    signature_path = Path("a.txt.invalid.sig")

    with pytest.raises(subprocess.CalledProcessError):
        client.verify(artifact_path, certificate_path, signature_path)
