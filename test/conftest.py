import os
import shutil
import tempfile
from pathlib import Path

import pytest  # type: ignore

from .client import SigstoreClient


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


@pytest.fixture(autouse=True)
def workspace():
    """
    Create a temporary workspace directory to perform the test in.
    """
    workspace = tempfile.TemporaryDirectory()

    # Move entire contents of artifacts directory into workspace
    artifacts_dir = Path(__file__).parent.parent / "artifacts"
    shutil.copytree(artifacts_dir, workspace.name, dirs_exist_ok=True)

    # Now change the current working directory to our workspace
    os.chdir(workspace.name)

    yield Path(workspace.name)
    workspace.cleanup()
