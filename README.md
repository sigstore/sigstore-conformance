sigstore-conformance
====================

<!--- @begin-badges@ --->
![CI](https://github.com/sigstore/sigstore-conformance/workflows/CI/badge.svg)
![Self-test](https://github.com/sigstore/sigstore-conformance/workflows/Self-test/badge.svg)
<!--- @end-badges@ --->

`sigstore-conformance` is a conformance testing suite for Sigstore clients.

This suite provides a high-level view of client behaviour as a whole and sets
out to answer questions such as:
- Does the client fail when given a signing certificate that isn't signed by
  the Fulcio root CA during the signing workflow?
- Does the client fail when given an invalid inclusion proof from Rekor during
  the verification workflow?
- Does the client fail when given an invalid signed certificate timestamp as
  part of the Fulcio response in the signing workflow?
- etc

An official Sigstore client specification is being worked on at the moment as
part of the [Sigstore Architecture Documentation](https://github.com/sigstore/architecture-docs).
Once it's complete, `sigstore-conformance` aims to be able to test a client's
adherence to the specification.

Some general testing principles for this suite are:
- *Tests should be "workflow" focused.* This testing suite is not about fuzzing
  every possible input to the client CLI or achieving code coverage.
- *Tests should exercise the entire client end-to-end rather than individual
  subsystems in isolation.* Tests should include all network interactions with
  Sigstore infrastructure such as Rekor, Fulcio, etc. These tests should run
  against Sigstore staging and production infrastructure as well as custom built
  mock services to test atypical scenarios.

## Usage

Simply add `sigstore/sigstore-conformance` to one of your workflows:

```yaml
jobs:
  conformance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: install
        run: python -m pip install .
      - uses: sigstore/sigstore-conformance@v0.0.10
        with:
          entrypoint: sigstore
```

The only required configuration is the `entrypoint` parameter which provides a
command to invoke the client. `sigstore-conformance` expects that the client
exposes a CLI that conforms to the protocol outlined [here](docs/cli_protocol.md).

In the example above, the workflow is installing [sigstore-python](https://github.com/sigstore/sigstore-python)
and providing `sigstore` as the `entrypoint` since this is the command used to
invoke the client.

## Development

Easiest way to run the conformance suite locally is with the provided virtual environment:
```sh
$ make dev
$ source env/bin/activate
(env) $
```

The test suite can be configured with
* `--entrypoint=$SIGSTORE_CLIENT` where SIGSTORE_CLIENT is path to a script that implements the
  [CLI specification](https://github.com/sigstore/sigstore-conformance/blob/main/docs/cli_protocol.md)
* `--identity-token=$GITHUB_TOKEN` where GITHUB_TOKEN is a GitHub token with actions:read
  access for public repositories (--identity-token is only required for signing tests)
* optional (and currently experimental) `--staging`: This instructs the test suite to run
  against Sigstore staging infrastructure
* The environment variable `GHA_SIGSTORE_CONFORMANCE_XFAIL` can be used to
  set expected results

```sh
(env) $ # run verification tests only
(env) $ pytest test --entrypoint=$SIGSTORE_CLIENT --skip-signing
(env) $ # run all tests
(env) $ pytest test --entrypoint=$SIGSTORE_CLIENT --identity-token=$GITHUB_TOKEN
```

Following examples run the included sigstore-python-conformance client script and use the
[`gh` CLI](https://cli.github.com/):
```sh
(env) $ # run verification tests only
(env) $ GHA_SIGSTORE_CONFORMANCE_XFAIL="test_verify_with_trust_root test_verify_dsse_bundle_with_trust_root" \
    pytest test --entrypoint=sigstore-python-conformance --skip-signing

(env) $ # run all tests
(env) $ GHA_SIGSTORE_CONFORMANCE_XFAIL="test_verify_with_trust_root test_verify_dsse_bundle_with_trust_root" \
    pytest test --entrypoint=sigstore-python-conformance --identity-token=$(gh auth token)
```

## Licensing

`sigstore-conformance` is licensed under the Apache 2.0 License.

## Code of Conduct

Everyone interacting with this project is expected to follow the
[sigstore Code of Conduct](https://github.com/sigstore/.github/blob/main/CODE_OF_CONDUCT.md)

## Security

Should you discover any security issues, please refer to sigstore's [security
process](https://github.com/sigstore/.github/blob/main/SECURITY.md).
