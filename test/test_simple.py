import pytest  # type: ignore

from test.conftest import _MakeMaterials

from .client import SigstoreClient


@pytest.mark.signing
@pytest.mark.staging
def test_simple(client: SigstoreClient, make_materials: _MakeMaterials) -> None:
    """
    A simple test that signs and verifies an artifact for a given Sigstore
    client.
    """

    input_path, materials = make_materials("a.txt")
    assert not materials.exists()

    # Sign the artifact.
    client.sign(materials, input_path)
    assert materials.exists()

    # Verify the artifact signature.
    client.verify(materials, input_path)
