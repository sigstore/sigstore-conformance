import os
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Tuple, TypeVar

import pytest  # type: ignore

from .client import (BundleMaterials, SignatureCertificateMaterials,
                     SigstoreClient, VerificationMaterials)

_M = TypeVar("_M", bound=VerificationMaterials)
_MakeMaterialsByType = Callable[[str, _M], Tuple[Path, _M]]
_MakeMaterials = Callable[[str], Tuple[Path, VerificationMaterials]]


def pytest_addoption(parser):
    """
    Add the `--entrypoint` flag to the `pytest` CLI.
    """
    parser.addoption(
        "--entrypoint",
        action="store",
        help="the command to invoke the Sigstore client under test",
        required=True,
        type=str,
    )


@pytest.fixture
def client(pytestconfig):
    """
    Parametrize each test with the client under test.
    """
    entrypoint = pytestconfig.getoption("--entrypoint")
    identity_token = pytestconfig.getoption("--identity-token")
    return SigstoreClient(entrypoint, identity_token)


@pytest.fixture
def make_materials_by_type() -> _MakeMaterialsByType:
    """
    Returns a function that constructs the requested subclass of
    `VerificationMaterials` alongside an appropriate input path.
    """

    def _make_materials_by_type(
        input_name: str, cls: VerificationMaterials
    ) -> Tuple[Path, VerificationMaterials]:
        input_path = Path(input_name)
        output = cls.from_input(input_path)

        return (input_path, output)

    return _make_materials_by_type


@pytest.fixture(params=[BundleMaterials, SignatureCertificateMaterials])
def make_materials(request, make_materials_by_type) -> _MakeMaterials:
    """
    Returns a function that constructs `VerificationMaterials` alongside an
    appropriate input path. The subclass of `VerificationMaterials` that is returned
    is parameterized across `BundleMaterials` and `SignatureCertificateMaterials`.

    See `make_materials_by_type` for a fixture that uses a specific subclass of
    `VerificationMaterials`.
    """

    def _make_materials(input_name: str):
        return make_materials_by_type(input_name, request.param)

    return _make_materials


@pytest.fixture(autouse=True)
def workspace():
    """
    Create a temporary workspace directory to perform the test in.
    """
    workspace = tempfile.TemporaryDirectory()

    # Move entire contents of artifacts directory into workspace
    assets_dir = Path(__file__).parent.parent / "test" / "assets"
    shutil.copytree(assets_dir, workspace.name, dirs_exist_ok=True)

    # Now change the current working directory to our workspace
    os.chdir(workspace.name)

    yield Path(workspace.name)
    workspace.cleanup()
