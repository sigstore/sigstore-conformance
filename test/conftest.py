import os
import shutil
import tempfile
from pathlib import Path

import pytest

from .client import SigstoreClient


def pytest_addoption(parser):
    """
    Add the `--entrypoint` flag to the `pytest` CLI.
    """
    parser.addoption(
        "--entrypoint",
        action="store",
        help="the entrypoint for the Sigstore client under test",
        required=True,
        type=str,
    )


def pytest_generate_tests(metafunc):
    """
    Parametrize each test with the client under test.
    """
    entrypoint = metafunc.config.option.entrypoint
    if "client" in metafunc.fixturenames and entrypoint is not None:
        metafunc.parametrize("client", [SigstoreClient(entrypoint)])


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
