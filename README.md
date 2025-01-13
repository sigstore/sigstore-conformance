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

1. Include an executable in your project that implements the
client-under-test [CLI protocol](docs/cli_protocol.md).
2. Use the `sigstore/sigstore-conformance` action in your test workflow:
    ```yaml
    jobs:
      conformance:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4

          # insert your client installation steps here

          # Run tests against production Sigstore environment
          - uses: sigstore/sigstore-conformance@v0.0.16
            with:
              entrypoint: my-conformance-client

          # Run tests against staging Sigstore environment
          - uses: sigstore/sigstore-conformance@v0.0.16
            with:
              entrypoint: my-conformance-client
              environment: staging
    ```

See [sigstore-python conformance test](https://github.com/sigstore/sigstore-python/blob/main/.github/workflows/conformance.yml)
for a complete example.

### `sigstore/sigstore-conformance` action inputs

The important action inputs are
* `entrypoint`: required string. A command that implements the client-under-test
  [CLI protocol](docs/cli_protocol.md)
* `environment`: 'production' (default) or 'staging'. This selects the Sigstore environment to
  run against
* `xfail`: optional string. Whitespace separated test names that are expected to fail.

See [action.yml](action.yml) for full list of inputs.

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
* optional `--staging`: This instructs the test suite to run against Sigstore staging infrastructure
* optional `--skip-signing`: Runs verification tests only
* The environment variable `GHA_SIGSTORE_CONFORMANCE_XFAIL` can be used to
  set expected failures

```sh
(env) $ # run all tests
(env) $ pytest test --entrypoint=$SIGSTORE_CLIENT
(env) $ # run verification tests only
(env) $ pytest test --entrypoint=$SIGSTORE_CLIENT --skip-signing
```

Following example runs the test suite with the included sigstore-python-conformance client script:
```sh
(env) $ # run all tests
(env) $ GHA_SIGSTORE_CONFORMANCE_XFAIL="test_verify_with_trust_root test_verify_dsse_bundle_with_trust_root" \
    pytest test --entrypoint=sigstore-python-conformance
```

## Licensing

`sigstore-conformance` is licensed under the Apache 2.0 License.

## Code of Conduct

Everyone interacting with this project is expected to follow the
[sigstore Code of Conduct](https://github.com/sigstore/.github/blob/main/CODE_OF_CONDUCT.md)

## Security

Should you discover any security issues, please refer to sigstore's [security
process](https://github.com/sigstore/.github/blob/main/SECURITY.md).
