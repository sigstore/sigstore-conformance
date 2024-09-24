import enum
import functools
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from base64 import b64decode
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TypeVar

import pytest

from .client import (
    BundleMaterials,
    SignatureCertificateMaterials,
    SigstoreClient,
    VerificationMaterials,
)

_M = TypeVar("_M", bound=VerificationMaterials)
_MakeMaterialsByType = Callable[[str, _M], tuple[Path, _M]]
_MakeMaterials = Callable[[str], tuple[Path, VerificationMaterials]]
_VerifyBundle = Callable[[VerificationMaterials, Path], None]

_OIDC_BEACON_API_URL = (
    "https://api.github.com/repos/sigstore-conformance/extremely-dangerous-public-oidc-beacon/"
    "actions"
)
_OIDC_BEACON_WORKFLOW_ID = 55399612

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


def _jwt_cache():
    def _decorator(fn: Callable[[any], str]):
        @functools.wraps(fn)
        def _wrapped(pytestconfig):
            if pytestconfig.getoption("--skip-signing"):
                return ""

            # Cache the token for the duration of the test run,
            # as long as the returned token is not yet expired
            if hasattr(_wrapped, "token"):
                min_validity = pytestconfig.getoption("--min-id-token-validity")
                if _is_valid_at(_wrapped.token, datetime.now() + min_validity):
                    return _wrapped.token

            token = fn(pytestconfig)
            _wrapped.token = token
            return token

        return _wrapped

    return _decorator


def _is_valid_at(token: str, reference_time: datetime) -> bool:
    # split token, b64 decode (with padding), parse as json, validate expiry
    payload = token.split(".")[1]
    payload += "=" * (4 - len(payload) % 4)
    payload_json = json.loads(b64decode(payload))

    expiry = datetime.fromtimestamp(payload_json["exp"])
    return reference_time < expiry


@pytest.fixture
@_jwt_cache()
def identity_token(pytestconfig) -> str:
    # following code is modified from extremely-dangerous-public-oidc-beacon download-token.py.
    # Caching can be made smarter (to return the cached token only if it is valid) if token
    # starts going invalid during runs
    MIN_VALIDITY = pytestconfig.getoption("--min-id-token-validity")
    MAX_RETRY_TIME = timedelta(minutes=5 if os.getenv("CI") else 1)
    RETRY_SLEEP_SECS = 30 if os.getenv("CI") else 5
    GIT_URL = "https://github.com/sigstore-conformance/extremely-dangerous-public-oidc-beacon.git"

    def git_clone(url: str, dir: str) -> None:
        base_cmd = ["git", "clone", "--quiet", "--branch", "current-token", "--depth", "1"]
        subprocess.run(base_cmd + [url, dir], check=True)

    start_time = datetime.now()
    while datetime.now() <= start_time + MAX_RETRY_TIME:
        with TemporaryDirectory() as tempdir:
            git_clone(GIT_URL, tempdir)

            with Path(tempdir, "oidc-token.txt").open() as f:
                token = f.read().rstrip()

            if _is_valid_at(token, datetime.now() + MIN_VALIDITY):
                return token

        print(f"Current token expires too early, retrying in {RETRY_SLEEP_SECS} seconds.")
        time.sleep(RETRY_SLEEP_SECS)

    raise TimeoutError(f"Failed to find a valid token in {MAX_RETRY_TIME}")


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
def make_materials_by_type() -> _MakeMaterialsByType:
    """
    Returns a function that constructs the requested subclass of
    `VerificationMaterials` alongside an appropriate input path.
    """

    def _make_materials_by_type(
        input_name: str, cls: VerificationMaterials
    ) -> tuple[Path, VerificationMaterials]:
        input_path = Path(input_name)
        output = cls.from_input(input_path)

        return input_path, output

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


class ArtifactInputType(enum.Enum):
    PATH = enum.auto()
    DIGEST = enum.auto()


@pytest.fixture(params=[ArtifactInputType.PATH, ArtifactInputType.DIGEST])
def verify_bundle(request, client) -> _VerifyBundle:
    """
    Returns a function that verifies an artifact using the given verification materials

    The fixture is parametrized to run twice, one verifying the artifact itself (passing
    the file path to the verification function), and another verifying the artifact's
    digest.
    """

    def _verify_bundle(materials: VerificationMaterials, input_path: Path) -> None:
        if request.param == ArtifactInputType.PATH:
            client.verify(materials, input_path)
        else:
            with open(input_path, "rb") as f:
                digest = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"
                client.verify(materials, digest)

    return _verify_bundle


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


@pytest.fixture(autouse=True)
def conformance_xfail(request):
    if request.node.originalname in _XFAIL_LIST:
        request.node.add_marker(pytest.mark.xfail(reason="skipped by suite runner", strict=True))
