from test.conftest import MakeMaterials

from .client import SigstoreClient


def test_simple(client: SigstoreClient, make_materials: MakeMaterials) -> None:
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
