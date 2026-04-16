import pytest  # type: ignore

from test.client import BundleMaterials
from test.conftest import _MakeMaterialsByType

from .client import SigstoreClient


@pytest.mark.signing
@pytest.mark.staging
def test_simple(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
) -> None:
    """
    A simple test that signs and verifies an artifact for a given Sigstore
    client.
    """

    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    assert not materials.exists()

    # Sign the artifact.
    client.sign(materials, input_path)
    assert materials.exists()

    # Verify the artifact signature with the client itself
    client.verify(materials, input_path)

    # Use selftest client verify to assert that the bundle is correctly formed
    selftest_client = SigstoreClient(
        str(project_root / "selftest-client"), client.identity_token, client.staging
    )
    selftest_client.verify(materials, input_path)
