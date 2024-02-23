#!/usr/bin/env python3

# action.py: run the sigstore-conformance test suite
#
# all state is passed in as environment variables

import os
import sys
from pathlib import Path

import pytest

_SUMMARY = Path(os.getenv("GITHUB_STEP_SUMMARY")).open("a")  # type: ignore
_RENDER_SUMMARY = os.getenv("GHA_SIGSTORE_CONFORMANCE_SUMMARY", "true") == "true"
_DEBUG = os.getenv("GHA_SIGSTORE_CONFORMANCE_INTERNAL_BE_CAREFUL_DEBUG", "false") != "false"
_ACTION_PATH = Path(os.getenv("GITHUB_ACTION_PATH"))  # type: ignore
_ENABLE_STAGING = os.getenv("GHA_SIGSTORE_CONFORMANCE_ENABLE_STAGING", "false").lower() == "true"


def _summary(msg):
    if _RENDER_SUMMARY:
        print(msg, file=_SUMMARY)


def _debug(msg):
    if _DEBUG:
        print(f"\033[93mDEBUG: {msg}\033[0m", file=sys.stderr)


def _sigstore_conformance(staging: bool) -> int:
    args = []

    if _DEBUG:
        args.extend(["-s", "-vv", "--showlocals"])

    entrypoint = os.getenv("GHA_SIGSTORE_CONFORMANCE_ENTRYPOINT")
    if entrypoint:
        args.extend(["--entrypoint", entrypoint])

    if staging:
        args.append("--staging")

    skip_signing = os.getenv("GHA_SIGSTORE_CONFORMANCE_SKIP_SIGNING", "false").lower() == "true"
    if skip_signing:
        args.extend(["--skip-signing"])

    gh_token = os.getenv("GHA_SIGSTORE_GITHUB_TOKEN")
    if gh_token:
        args.extend(["--github-token", gh_token])

    infra = "staging" if staging else "production"
    print(f"running sigstore-conformance against Sigstore {infra} infrastructure")
    _debug(f"running: sigstore-conformance {[str(a) for a in args]}")

    return pytest.main([str(_ACTION_PATH / "test"), *args])


# Run against production, then optionally against staging
status = _sigstore_conformance(staging=False)
if _ENABLE_STAGING:
    status += _sigstore_conformance(staging=True)

if status == 0:
    _summary("🎉 sigstore-conformance exited successfully")
else:
    _summary("❌ sigstore-conformance found one or more test failures")

sys.exit(status)
