import enum
import functools
import json
import os
import shutil
import subprocess
import tempfile
from base64 import b64decode
from collections.abc import Callable
from datetime import timedelta
from fnmatch import fnmatch
from pathlib import Path
from typing import TypeVar
from urllib import parse

import platformdirs
import pytest
from urllib3 import request

from .client import (
    BundleMaterials,
    SigstoreClient,
    VerificationMaterials,
)

_M = TypeVar("_M", bound=VerificationMaterials)
_MakeMaterialsByType = Callable[[str, _M], _M]
_MakeMaterials = Callable[[str], VerificationMaterials]
_VerifyBundle = Callable[[VerificationMaterials], None]

_XFAIL_LIST = os.getenv("GHA_SIGSTORE_CONFORMANCE_XFAIL", "").split()


class OidcTokenError(Exception):
    pass


class ConfigError(Exception):
    pass


def pytest_addoption(parser) -> None:
    """Add `--entrypoint` and `--skip-signing` flags to CLI."""
    parser.addoption(
        "--entrypoint",
        action="store",
        help="the command to invoke the Sigstore client under test",
        required=True,
        type=str,
    )
    parser.addoption(
        "--skip-signing",
        action="store_true",
        help="skip tests that require signing functionality",
    )
    parser.addoption(
        "--staging",
        action="store_true",
        help="run tests against staging",
    )
    parser.addoption(
        "--min-id-token-validity",
        action="store",
        help="Minimum validity of the identity token in seconds",
        type=lambda x: timedelta(seconds=int(x)),
        default=timedelta(seconds=20),
    )


def pytest_runtest_setup(item):
    if "signing" in item.keywords and item.config.getoption("--skip-signing"):
        pytest.skip("skipping test that requires signing support due to `--skip-signing` flag")
    if "staging" not in item.keywords and item.config.getoption("--staging"):
        pytest.skip("skipping test that does not support staging yet due to `--staging` flag")


def pytest_configure(config):
    config.addinivalue_line("markers", "signing: mark test as requiring signing functionality")
    config.addinivalue_line("markers", "staging: mark test as supporting testing against staging")


def pytest_internalerror(excrepr, excinfo):
    if excinfo.type == ConfigError:
        print(excinfo.value)
        return True

    return False


@pytest.fixture
@functools.cache
def identity_token() -> str:
    resp = request(
        "GET",
        "https://storage.googleapis.com/sigstore-test-identity-token/untrusted-testing-token.txt",
        timeout=30.0,
    )
    return resp.data.decode()


@pytest.fixture
def client(pytestconfig, identity_token):
    """
    Parametrize each test with the client under test.
    """
    entrypoint = pytestconfig.getoption("--entrypoint")
    if not os.path.isabs(entrypoint):
        entrypoint = os.path.join(pytestconfig.invocation_params.dir, entrypoint)

    staging = pytestconfig.getoption("--staging")

    return SigstoreClient(entrypoint, identity_token, staging)


@pytest.fixture
def project_root(request) -> Path:
    """
    Returns the repository root directory.
    """
    return request.config.rootpath


@pytest.fixture
def make_materials_by_type() -> _MakeMaterialsByType:
    """
    Returns a function that constructs the requested subclass of
    `VerificationMaterials` alongside an appropriate input path.
    """

    def _make_materials_by_type(
        input_name: str, cls: VerificationMaterials
    ) -> VerificationMaterials:
        input_path = Path(input_name)
        return cls.from_artifact_path(input_path)

    return _make_materials_by_type


@pytest.fixture(params=[BundleMaterials])
def make_materials(request, make_materials_by_type) -> _MakeMaterials:
    """
    Returns a function that constructs `VerificationMaterials` alongside an
    appropriate input path. The subclass of `VerificationMaterials` that is returned
    is parameterized across `BundleMaterials`.

    See `make_materials_by_type` for a fixture that uses a specific subclass of
    `VerificationMaterials`.
    """

    def _make_materials(input_name: str):
        return make_materials_by_type(input_name, request.param)

    return _make_materials


class ArtifactInputType(enum.Enum):
    PATH = enum.auto()
    DIGEST = enum.auto()

    def __str__(self) -> str:
        return "PATH" if self == ArtifactInputType.PATH else "DIGEST"


@pytest.fixture(params=[ArtifactInputType.PATH, ArtifactInputType.DIGEST])
def verify_bundle(request, client) -> _VerifyBundle:
    """
    Returns a function that verifies an artifact using the given verification materials

    The fixture is parameterized to run twice, one verifying the artifact itself (passing
    the file path to the verification function), and another verifying the artifact's
    digest.
    """

    def _verify_bundle(materials: VerificationMaterials) -> None:
        if request.param == ArtifactInputType.PATH:
            client.verify(materials)
        else:
            client.verify_digest(materials)

    return _verify_bundle


@pytest.fixture(autouse=True)
def workspace(project_root: Path):
    """
    Create a temporary workspace directory to perform the test in.
    """
    workspace = tempfile.TemporaryDirectory()

    # Move entire contents of artifacts directory into workspace
    assets_dir = project_root / "test" / "assets"
    shutil.copytree(assets_dir, workspace.name, dirs_exist_ok=True)

    # Now change the current working directory to our workspace
    os.chdir(workspace.name)

    yield Path(workspace.name)
    workspace.cleanup()


@pytest.fixture(autouse=True)
def conformance_xfail(request):
    if any([fnmatch(request.node.name, xfail_pattern) for xfail_pattern in _XFAIL_LIST]):
        request.node.add_marker(pytest.mark.xfail(reason="skipped by suite runner", strict=True))


def pytest_generate_tests(metafunc):
    """
    Parametrize bundle_verify tests over all sudirectories under assets/bundle-verify
    """
    if "bundle_verify_dir" in metafunc.fixturenames:
        asset_root = Path(__file__).parent / "assets" / "bundle-verify"
        directories = [d for d in asset_root.iterdir() if d.is_dir()]
        dir_paths = [str(d) for d in directories]
        metafunc.parametrize("bundle_verify_dir", dir_paths, ids=[d.name for d in directories])


def _client_config(project_root: Path, staging: bool) -> tuple[Path, Path]:
    """Return paths to (up-to-date) TrustedRoot and SigningConfig

    This uses the internal selftest client feature 'update-trust-root'
    """
    if staging:
        cmd = [str(project_root / "selftest-client"), "--staging", "update-trust-root"]
        repo = parse.quote("https://tuf-repo-cdn.sigstage.dev", safe="")
    else:
        cmd = [str(project_root / "selftest-client"), "update-trust-root"]
        repo = parse.quote("https://tuf-repo-cdn.sigstore.dev", safe="")

    # run the selftest client to update files in sigstore-python cache
    subprocess.run(cmd, check=True)

    # then find files in sigstore-python cache
    cache_dir = platformdirs.user_cache_path("sigstore-python") / "tuf" / repo
    tr = cache_dir / "trusted_root.json"
    sc = cache_dir / "signing_config.v0.2.json"
    assert tr.exists()
    assert sc.exists()

    return (tr, sc)


@pytest.fixture
@functools.cache
def staging_config(project_root: Path) -> tuple[Path, Path]:
    """Return paths to (up-to-date) Staging TrustedRoot and SigningConfig"""
    return _client_config(project_root, staging=True)


@pytest.fixture
@functools.cache
def production_config(project_root: Path) -> tuple[Path, Path]:
    """Return paths to (up-to-date) Production TrustedRoot and SigningConfig"""
    return _client_config(project_root, staging=False)
