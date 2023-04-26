#!/usr/bin/env python3

# action.py: run the sigstore-conformance test suite
#
# all state is passed in as environment variables

import os
import string
import subprocess
import sys
import time
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests

_HERE = Path(__file__).parent.resolve()
_TEMPLATES = _HERE / "templates"

_SUMMARY = Path(os.getenv("GITHUB_STEP_SUMMARY")).open("a")  # type: ignore
_RENDER_SUMMARY = os.getenv("GHA_SIGSTORE_CONFORMANCE_SUMMARY", "true") == "true"
_DEBUG = (
    os.getenv("GHA_SIGSTORE_CONFORMANCE_INTERNAL_BE_CAREFUL_DEBUG", "false") != "false"
)
_ACTION_PATH = Path(os.getenv("GITHUB_ACTION_PATH"))  # type: ignore
_OIDC_BEACON_API_URL = (
    "https://api.github.com/repos/sigstore-conformance/extremely-dangerous-public-oidc-beacon/"
    "actions"
)
_OIDC_BEACON_WORKFLOW_ID = 55399612


class OidcTokenError(Exception):
    pass


def _get_oidc_token(gh_token: str) -> str:
    session = requests.Session()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {gh_token}",
    }

    workflow_time: Optional[datetime] = None
    run_id: str

    # We need a token that was generated in the last 5 minutes. Keep checking until we find one.
    while workflow_time is None or datetime.now() - workflow_time >= timedelta(
        minutes=5
    ):
        # If there's a lot of traffic in the GitHub Actions cron queue, we might not have a valid
        # token to use. In that case, wait for 30 seconds and try again.
        if workflow_time is not None:
            _log("Couldn't find a recent token, waiting...")
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
        workflow_time = datetime.strptime(
            workflow_run["run_started_at"], "%Y-%m-%dT%H:%M:%SZ"
        )

    resp = session.get(
        url=_OIDC_BEACON_API_URL + f"/runs/{run_id}/artifacts",
        headers=headers,
    )
    resp.raise_for_status()

    resp_json = resp.json()
    artifacts = resp_json["artifacts"]
    if len(artifacts) != 1:
        raise OidcTokenError(
            f"Found unexpected number of artifacts on OIDC beacon run: {artifacts}"
        )

    oidc_artifact = artifacts[0]
    if oidc_artifact["name"] != "oidc-token":
        raise OidcTokenError(
            f"Found unexpected artifact on OIDC beacon run: {oidc_artifact['name']}"
        )
    artifact_id = oidc_artifact["id"]

    # Download the OIDC token artifact and unzip the archive.
    resp = session.get(
        url=_OIDC_BEACON_API_URL + f"/artifacts/{artifact_id}/zip",
        headers=headers,
    )
    resp.raise_for_status()

    with ZipFile(BytesIO(resp.content)) as artifact_zip:
        artifact_file = artifact_zip.open("oidc-token.txt")

        # NOTE(alex): Strip newline.
        return artifact_file.read().decode()[:-1]


def _template(name):
    path = _TEMPLATES / f"{name}.md"
    return string.Template(path.read_text())


def _summary(msg):
    if _RENDER_SUMMARY:
        print(msg, file=_SUMMARY)


def _debug(msg):
    if _DEBUG:
        print(f"\033[93mDEBUG: {msg}\033[0m", file=sys.stderr)


def _log(msg):
    print(msg, file=sys.stderr)


def _sigstore_conformance(*args):
    return ["pytest", _ACTION_PATH / "test", *args]


def _fatal_help(msg):
    print(f"::error::❌ {msg}")
    sys.exit(1)


sigstore_conformance_args = []

if _DEBUG:
    sigstore_conformance_args.extend(["-s", "-vv", "--showlocals"])

entrypoint = os.getenv("GHA_SIGSTORE_CONFORMANCE_ENTRYPOINT")
if entrypoint:
    sigstore_conformance_args.extend(["--entrypoint", entrypoint])

gh_token = os.getenv("GHA_SIGSTORE_CONFORMANCE_GITHUB_TOKEN")
if gh_token:
    try:
        oidc_token = _get_oidc_token(gh_token)
    except OidcTokenError as e:
        _fatal_help(f"Could not retrieve OIDC token: {str(e)}")
    sigstore_conformance_args.extend(["--identity-token", oidc_token])

_debug(f"running: sigstore-conformance {[str(a) for a in sigstore_conformance_args]}")

status = subprocess.run(
    _sigstore_conformance(*sigstore_conformance_args),
    text=True,
    capture_output=True,
)

_debug(status.stdout)

if status.returncode == 0:
    _summary("🎉 sigstore-conformance exited successfully")
else:
    _summary("❌ sigstore-conformance found one or more test failures")

_summary(
    """
<details>
<summary>
    Raw `sigstore-conformance` output
</summary>

```
    """
)
_log(status.stdout)
_summary(
    """
```
</details>
    """
)

sys.exit(status.returncode)
