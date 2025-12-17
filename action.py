#!/usr/bin/env python3

# action.py: run the sigstore-conformance test suite
#
# all state is passed in as environment variables

import json
import os
import sys
from pathlib import Path

import pytest

_SUMMARY = Path(os.getenv("GITHUB_STEP_SUMMARY")).open("a")  # type: ignore
_RENDER_SUMMARY = os.getenv("GHA_SIGSTORE_CONFORMANCE_SUMMARY", "true") == "true"
_DEBUG = os.getenv("GHA_SIGSTORE_CONFORMANCE_INTERNAL_BE_CAREFUL_DEBUG", "false") != "false"
_ACTION_PATH = Path(os.getenv("GITHUB_ACTION_PATH"))  # type: ignore


def _summary(msg):
    if _RENDER_SUMMARY:
        print(msg, file=_SUMMARY)


def _debug(msg):
    if _DEBUG:
        print(f"\033[93mDEBUG: {msg}\033[0m", file=sys.stderr)


def _sigstore_conformance(environment: str) -> int:
    args = ["--json-report", "--json-report-file=conformance-report.json", "--durations=0"]

    if _DEBUG:
        args.extend(["-s", "-vv", "--showlocals"])

    entrypoint = os.getenv("GHA_SIGSTORE_CONFORMANCE_ENTRYPOINT")
    if entrypoint:
        args.append(f"--entrypoint={entrypoint}")

    if environment == "staging":
        args.append("--staging")
    elif environment != "production":
        raise ValueError(f"Unknown environment '{environment}'")

    skip_signing = os.getenv("GHA_SIGSTORE_CONFORMANCE_SKIP_SIGNING", "false").lower() == "true"
    if skip_signing:
        args.extend(["--skip-signing"])

    print(f"running sigstore-conformance against Sigstore {environment} infrastructure")
    _debug(f"running: sigstore-conformance {[str(a) for a in args]}")

    status = pytest.main([str(_ACTION_PATH / "test"), *args])

    # Inject some metadata into the report
    with open("conformance-report.json", "r+") as f:
        report_data = json.load(f)
        if "environment" not in report_data:
            report_data["environment"] = {}
        client_sha = os.getenv("GHA_SIGSTORE_CONFORMANCE_CLIENT_SHA")
        if client_sha:
            report_data["environment"]["client_sha"] = client_sha
        client_sha_url = os.getenv("GHA_SIGSTORE_CONFORMANCE_CLIENT_SHA_URL")
        if client_sha_url:
            report_data["environment"]["client_sha_url"] = client_sha_url
        workflow_run = os.getenv("GHA_SIGSTORE_CONFORMANCE_WORKFLOW_RUN")
        if workflow_run:
            report_data["environment"]["workflow_run"] = workflow_run
        f.seek(0)
        json.dump(report_data, f, indent=4)
        f.truncate()

    return status


# Run against chosen environment
environment = os.getenv("GHA_SIGSTORE_CONFORMANCE_ENVIRONMENT", "production")
status = _sigstore_conformance(environment)

if status == 0:
    _summary("🎉 sigstore-conformance exited successfully")
else:
    _summary("❌ sigstore-conformance found one or more test failures")

sys.exit(status)
