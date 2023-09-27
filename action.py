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


def _summary(msg):
    if _RENDER_SUMMARY:
        print(msg, file=_SUMMARY)


def _debug(msg):
    if _DEBUG:
        print(f"\033[93mDEBUG: {msg}\033[0m", file=sys.stderr)


def _sigstore_conformance(*args) -> int:
    return pytest.main([str(_ACTION_PATH / "test"), *args])


sigstore_conformance_args = []

if _DEBUG:
    sigstore_conformance_args.extend(["-s", "-vv", "--showlocals"])

entrypoint = os.getenv("GHA_SIGSTORE_CONFORMANCE_ENTRYPOINT")
if entrypoint:
    sigstore_conformance_args.extend(["--entrypoint", entrypoint])

skip_signing = os.getenv("GHA_SIGSTORE_CONFORMANCE_SKIP_SIGNING", "false").lower() == "true"
if skip_signing:
    sigstore_conformance_args.extend(["--skip-signing"])

supports_trustedroot = (
    os.getenv("GHA_SIGSTORE_CONFORMANCE_SUPPORTS_TRUSTED_ROOT", "false").lower() == "true"
)
if supports_trustedroot:
    sigstore_conformance_args.extend(["--supports-trusted-root"])

gh_token = os.getenv("GHA_SIGSTORE_GITHUB_TOKEN")
if gh_token:
    sigstore_conformance_args.extend(["--github-token", gh_token])

_debug(f"running: sigstore-conformance {[str(a) for a in sigstore_conformance_args]}")

status = _sigstore_conformance(*sigstore_conformance_args)

if status == 0:
    _summary("🎉 sigstore-conformance exited successfully")
else:
    _summary("❌ sigstore-conformance found one or more test failures")


sys.exit(status)
