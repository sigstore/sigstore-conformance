from pathlib import Path

import pytest  # type: ignore

from .client import (BundleMaterials, SignatureCertificateMaterials,
                     SigstoreClient, VerificationMaterials)

_input_path = Path("a.txt")
_materials = [
    BundleMaterials.from_input(_input_path),
    SignatureCertificateMaterials.from_input(_input_path),
]


@pytest.mark.parametrize("materials", _materials)
def test_simple(client: SigstoreClient, materials: VerificationMaterials) -> None:
    """
    A simple test that signs and verifies an artifact for a given Sigstore
    client.
    """
    assert not materials.exists()

    # Sign the artifact.
    client.sign(materials, _input_path)
    assert materials.exists()

    # Verify the artifact signature.
    client.verify(materials, _input_path)
