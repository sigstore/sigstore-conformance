sigstore-conformance
====================

<!--- @begin-badges@ --->
![CI](https://github.com/trailofbits/sigstore-conformance/workflows/CI/badge.svg)
![Self-test](https://github.com/trailofbits/sigstore-conformance/workflows/Self-test/badge.svg)
<!--- @end-badges@ --->

`sigstore-conformance` is a conformance testing suite for Sigstore clients.

This suite provides a high-level view of client behaviour as a whole and sets
out to answer questions such as:
- What files are written to the disk by the client in what situations?
- Does the client fail when given a signing certificate that isn't signed by
  the Fulcio root CA during the signing workflow?
- Does the client fail when given an invalid inclusion proof from Rekor during
  the verification workflow?
- Does the client fail when given an invalid signed certificate timestamp as
  part of the Fulcio response in the signing workflow?
- etc

Over time, `sigstore-conformance` aims to become an informal specification that
describes how Sigstore clients are expected to behave.

Some general testing principles for this suite are:
- *Tests should be "workflow" focused.* This testing suite is not about fuzzing
  every possible input to the client CLI or achieving code coverage.
- *Tests should exercise the entire client end-to-end rather than individual
  subsystems in isolation.* Tests should include all network interactions with
  Sigstore infrastructure such as Rekor, Fulcio, etc. These tests should run
  against Sigstore staging and production infrastructure as well as custom built
  mock services to test atypical scenarios.

## Usage

Simply create a new workflow file at `.github/workflows/conformance.yml` and add
the `trailofbits/sigstore-conformance` action to it.

```yaml
jobs:
  conformance:
    permissions:
      id-token: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: install
        run: python -m pip install .
      - uses: trailofbits/sigstore-conformance@v0.0.1
        with:
          entrypoint: sigstore
```

The only required configuration is the `entrypoint` parameter which provides a
command to invoke the client. `sigstore-conformance` expects that the client
exposes a CLI that conforms to the protocol outlined [here](docs/cli_protocol.md).

In the example above, the workflow is installing [sigstore-python](https://github.com/sigstore/sigstore-python)
and providing `sigstore` as the `entrypoint` since this is the command used to
invoke the client.

The workflow that uses this action **must** be at
`.github/workflows/conformance.yml`. This is a current limitation of the test
suite and is required to reliably verify signing certificates.

The relevant job must have permission to request the OIDC token to authenticate
with. This can be done by adding a `permission` setting within the job that
invokes the `trailofbits/sigstore-conformance` action.

```yaml
conformance:
  permissions:
    id-token: write
```

More information about permission settings can be found [here](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect#adding-permissions-settings).

## Licensing

`sigstore-conformance` is licensed under the Apache 2.0 License.

## Code of Conduct

Everyone interacting with this project is expected to follow the
[sigstore Code of Conduct](https://github.com/sigstore/.github/blob/main/CODE_OF_CONDUCT.md)

## Security

Should you discover any security issues, please refer to sigstore's [security
process](https://github.com/sigstore/.github/blob/main/SECURITY.md).
