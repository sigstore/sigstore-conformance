sigstore-conformance
====================

<!--- @begin-badges@ --->
![CI](https://github.com/trailofbits/sigstore-conformance/workflows/CI/badge.svg)
![Self-test](https://github.com/trailofbits/sigstore-conformance/workflows/Self-test/badge.svg)
<!--- @end-badges@ --->

`sigstore-conformance` is a conformance testing suite for Sigstore clients.

## Usage

Simply add `trailofbits/sigstore-conformance` to one of your workflows.

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
