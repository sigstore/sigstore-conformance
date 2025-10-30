#!/usr/bin/env bash

set -eo pipefail

die() {
  echo "::error::${1}"
  exit 1
}

# NOTE: This file is meant to be sourced, not executed as a script.
if [[ "${0}" == "${BASH_SOURCE[0]}" ]]; then
  die "Internal error: setup harness was executed instead of being sourced?"
fi

# We expect cpython-release-tracker to have been checked out;
# the unit tests expect to load its assets.
if [[ ! -d "${GITHUB_WORKSPACE}/cpython-release-tracker" ]]; then
  die "cpython-release-tracker is not checked out!"
fi

# Check the Python version, making sure it's new enough (3.7+)
# The installation step immediately below will technically catch this,
# but doing it explicitly gives us the opportunity to produce a better
# error message.
vers=$(python -V | cut -d ' ' -f2)
maj_vers=$(cut -d '.' -f1 <<< "${vers}")
min_vers=$(cut -d '.' -f2 <<< "${vers}")

[[ "${maj_vers}" == "3" && "${min_vers}" -ge 7 ]] || die "Bad Python version: ${vers}"

# Install test suite
${GITHUB_ACTION_PATH}/setup/create-venv.sh sigstore-conformance-env
. ./sigstore-conformance-env/bin/activate && uv pip install --requirement "${GITHUB_ACTION_PATH}/requirements.txt"

# Signing test uses selftest client to verify the bundle: install selftest client as well
${GITHUB_ACTION_PATH}/setup/create-venv.sh sigstore-conformance-selftest-env
. ./sigstore-conformance-selftest-env/bin/activate && uv  pip install --requirement "${GITHUB_ACTION_PATH}/selftest-requirements.txt"
