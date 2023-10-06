import os
import shutil
import tempfile
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import TypeVar
from zipfile import ZipFile

import pytest
import requests

from .client import (
    BundleMaterials,
    SignatureCertificateMaterials,
    SigstoreClient,
    VerificationMaterials,
)

_M = TypeVar("_M", bound=VerificationMaterials)
_MakeMaterialsByType = Callable[[str, _M], tuple[Path, _M]]
_MakeMaterials = Callable[[str], tuple[Path, VerificationMaterials]]

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
    """
    Add the `--entrypoint`, `--github-token`, and `--skip-signing` flags to
    the `pytest` CLI.
    """
    parser.addoption(
        "--entrypoint",
        action="store",
        help="the command to invoke the Sigstore client under test",
        required=True,
        type=str,
    )
    parser.addoption(
        "--github-token",
        action="store",
        help="the GitHub token to supply to the Sigstore client under test",
        type=str,
    )
    parser.addoption(
        "--skip-signing",
        action="store_true",
        help="skip tests that require signing functionality",
    )


def pytest_runtest_setup(item):
    if "signing" in item.keywords and item.config.getoption("--skip-signing"):
        pytest.skip("skipping test that requires signing support due to `--skip-signing` flag")


def pytest_configure(config):
    if not config.getoption("--github-token") and not config.getoption("--skip-signing"):
        raise ConfigError("Please specify one of '--github-token' or '--skip-signing'")

    config.addinivalue_line("markers", "signing: mark test as requiring signing functionality")


def pytest_internalerror(excrepr, excinfo):
    if excinfo.type == ConfigError:
        print(excinfo.value)
        return True

    return False


@pytest.fixture
def identity_token(pytestconfig) -> str:
    if pytestconfig.getoption("--skip-signing"):
        return ""

    gh_token = pytestconfig.getoption("--github-token")
    session = requests.Session()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {gh_token}",
    }

    workflow_time: datetime | None = None
    run_id: str

    # We need a token that was generated in the last 5 minutes. Keep checking until we find one.
    while workflow_time is None or datetime.now() - workflow_time >= timedelta(minutes=5):
        # If there's a lot of traffic in the GitHub Actions cron queue, we might not have a valid
        # token to use. In that case, wait for 30 seconds and try again.
        if workflow_time is not None:
            # FIXME(jl): logging in pytest?
            # _log("Couldn't find a recent token, waiting...")
            time.sleep(30)

        resp: requests.Response = session.get(
            url=_OIDC_BEACON_API_URL + f"/workflows/{_OIDC_BEACON_WORKFLOW_ID}/runs",
            headers=headers,
        )
        resp.raise_for_status()

        resp_json = resp.json()
        workflow_runs = resp_json["workflow_runs"]
        if not workflow_runs:
            raise OidcTokenError(f"Found no workflow runs: {resp_json}")

        workflow_run = workflow_runs[0]

        # If the job is still running, the token artifact won't have been generated yet.
        if workflow_run["status"] != "completed":
            continue

        run_id = workflow_run["id"]
        workflow_time = datetime.strptime(workflow_run["run_started_at"], "%Y-%m-%dT%H:%M:%SZ")

    resp = session.get(
        url=_OIDC_BEACON_API_URL + f"/runs/{run_id}/artifacts",
        headers=headers,
    )
    resp.raise_for_status()

    resp_json = resp.json()
    try:
        artifact_id = next(a["id"] for a in resp_json["artifacts"] if a["name"] == "oidc-token")
    except StopIteration:
        raise OidcTokenError("Artifact 'oidc-token' could not be found")

    # Download the OIDC token artifact and unzip the archive.
    resp = session.get(
        url=_OIDC_BEACON_API_URL + f"/artifacts/{artifact_id}/zip",
        headers=headers,
    )
    resp.raise_for_status()

    with ZipFile(BytesIO(resp.content)) as artifact_zip:
        artifact_file = artifact_zip.open("oidc-token.txt")

        # Strip newline.
        return artifact_file.read().decode().rstrip()


@pytest.fixture
def client(pytestconfig, identity_token):
    """
    Parametrize each test with the client under test.
    """
    entrypoint = pytestconfig.getoption("--entrypoint")
    return SigstoreClient(entrypoint, identity_token)


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


@pytest.fixture(autouse=True)
def conformance_xfail(request):
    if request.node.originalname in _XFAIL_LIST:
        request.node.add_marker(pytest.mark.xfail(reason="skipped by suite runner", strict=True))
