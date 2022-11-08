import os
import subprocess
from pathlib import Path

import pytest  # type: ignore

from .client import SigstoreClient


def _swap_files(a: Path, b: Path) -> None:
    tmp_path = Path("tmp.txt")
    os.rename(a, tmp_path)
    os.rename(b, a)
    os.rename(tmp_path, b)


def test_verify_empty(client: SigstoreClient) -> None:
    """
    Tests that verification fails with empty certificates and signatures.
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

    # Write a blank temporary file.
    empty_path = Path("empty.txt")
    empty_path.open("w").close()
    _swap_files(artifact_path, empty_path)

    # Verify with an empty artifact.
    with pytest.raises(subprocess.CalledProcessError):
        client.verify(artifact_path, certificate_path, signature_path)

    _swap_files(empty_path, artifact_path)
    _swap_files(certificate_path, empty_path)

    # Verify with an empty certificate.
    with pytest.raises(subprocess.CalledProcessError):
        client.verify(artifact_path, certificate_path, signature_path)

    _swap_files(empty_path, certificate_path)
    _swap_files(signature_path, empty_path)

    # Verify with an empty signature.
    with pytest.raises(subprocess.CalledProcessError):
        client.verify(artifact_path, certificate_path, signature_path)

    _swap_files(empty_path, signature_path)

    # Verify with correct inputs.
    client.verify(artifact_path, certificate_path, signature_path)


def test_verify_mismatch(client: SigstoreClient) -> None:
    """
    Tests that verification fails with mismatching artifacts, certificates and
    signatures.
    """
    a_artifact_path = Path("a.txt")
    a_certificate_path = Path("a.txt.crt")
    a_signature_path = Path("a.txt.sig")

    assert a_artifact_path.exists()
    assert not a_certificate_path.exists()
    assert not a_signature_path.exists()

    # Sign a.txt.
    client.sign(a_artifact_path, a_certificate_path, a_signature_path)

    assert a_certificate_path.exists()
    assert a_signature_path.exists()

    # Sign b.txt.
    b_artifact_path = Path("b.txt")
    b_certificate_path = Path("b.txt.crt")
    b_signature_path = Path("b.txt.sig")

    client.sign(b_artifact_path, b_certificate_path, b_signature_path)

    assert b_certificate_path.exists()
    assert b_signature_path.exists()

    # Verify with a mismatching artifact.
    with pytest.raises(subprocess.CalledProcessError):
        client.verify(b_artifact_path, a_certificate_path, a_signature_path)

    # Verify with a mismatching certificate.
    with pytest.raises(subprocess.CalledProcessError):
        client.verify(a_artifact_path, b_certificate_path, a_signature_path)

    # Verify with a mismatching signature.
    with pytest.raises(subprocess.CalledProcessError):
        client.verify(a_artifact_path, a_certificate_path, b_signature_path)

    # Verify with correct inputs.
    client.verify(a_artifact_path, a_certificate_path, a_signature_path)
