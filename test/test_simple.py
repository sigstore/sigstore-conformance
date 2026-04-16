from pathlib import Path

import pytest  # type: ignore

from test.client import BundleMaterials
from test.conftest import _MakeMaterialsByType

from .client import SigstoreClient


@pytest.mark.signing
@pytest.mark.staging
def test_simple(
    client: SigstoreClient,
    make_materials_by_type: _MakeMaterialsByType,
    project_root: Path,
) -> None:
    """
    A simple test that signs and verifies an artifact for a given Sigstore
    client.
    """

    materials = make_materials_by_type("a.txt", BundleMaterials)
    materials.identity = (
        "untrusted-sigstore-test-id@sigstore-infra-playground.iam.gserviceaccount.com"
    )
    materials.issuer = "https://accounts.google.com"
    assert not materials.exists()

    # Sign the artifact.
    client.sign(materials)
    assert materials.exists()

    # Verify the artifact signature with the client itself
    client.verify(materials)

    # Use selftest client verify to assert that the bundle is correctly formed
    selftest_client = SigstoreClient(
        str(project_root / "selftest-client"), client.identity_token, client.staging
    )
    selftest_client.verify(materials)
