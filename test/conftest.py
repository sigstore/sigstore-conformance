import os
import shutil
import tempfile
from pathlib import Path
from typing import Tuple

import pytest  # type: ignore

from .client import (BundleMaterials, SignatureCertificateMaterials,
                     SigstoreClient, VerificationMaterials)


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
    return SigstoreClient(entrypoint)


@pytest.fixture
def construct_materials_for_cls():
    def _materials(
        input_name: str, mats_cls: VerificationMaterials
    ) -> Tuple[Path, VerificationMaterials]:
        input_path = Path(input_name)
        output = mats_cls.from_input(input_path)

        return (input_path, output)

    return _materials


@pytest.fixture(params=[BundleMaterials, SignatureCertificateMaterials])
def construct_materials(request, construct_materials_for_cls):
    def _curry(input_name: str):
        construct_materials_for_cls(input_name, request.param)

    return _curry


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
