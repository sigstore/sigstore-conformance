#!/usr/bin/env python3

# action.py: run the sigstore-conformance test suite
#
# all state is passed in as environment variables

import os
import string
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent.resolve()
_TEMPLATES = _HERE / "templates"

_SUMMARY = Path(os.getenv("GITHUB_STEP_SUMMARY")).open("a")  # type: ignore
_RENDER_SUMMARY = os.getenv("GHA_SIGSTORE_CONFORMANCE_SUMMARY", "true") == "true"
_DEBUG = (
    os.getenv("GHA_SIGSTORE_CONFORMANCE_INTERNAL_BE_CAREFUL_DEBUG", "false") != "false"
)
_ACTION_PATH = Path(os.getenv("GITHUB_ACTION_PATH"))  # type: ignore


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
    return ["pytest", *args, _ACTION_PATH / "test"]


def _fatal_help(msg):
    print(f"::error::❌ {msg}")
    sys.exit(1)


sigstore_conformance_args = []

if _DEBUG:
    sigstore_conformance_args.extend(["-s", "-vv"])

entrypoint = os.getenv("GHA_SIGSTORE_CONFORMANCE_ENTRYPOINT")
if entrypoint:
    sigstore_conformance_args.extend(["--entrypoint", entrypoint])

_debug(f"running: sigstore-conformance {[str(a) for a in sigstore_conformance_args]}")

status = subprocess.run(
    _sigstore_conformance(*sigstore_conformance_args),
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
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
