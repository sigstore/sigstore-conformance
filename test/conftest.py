import itertools
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from .container import Container
from .matrix import ReleaseChannelChoice, SigstoreClientChoice

_ALL_IMPLS = list(itertools.product(SigstoreClientChoice, ReleaseChannelChoice))


def pytest_generate_tests(metafunc):
    """
    Parametrize tests with each permutation of sigstore client and release channel.
    """
    if "client" in metafunc.fixturenames:
        metafunc.parametrize(
            ["client"],
            map(lambda perm: (perm[0].to_client(Container(*perm)),), _ALL_IMPLS),
        )


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
