sigstore-conformance
====================

<!--- @begin-badges@ --->
![CI](https://github.com/trailofbits/sigstore-conformance/workflows/CI/badge.svg)
![Self-test](https://github.com/trailofbits/sigstore-conformance/workflows/Self-test/badge.svg)
<!--- @end-badges@ --->

`sigstore-conformance` is a conformance testing suite for Sigstore clients.

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

### Running conformance testing in pull requests

In order to run this action in pull requests, there are some extra requirements
that must be met.

- Use the `pull_request_target` workflow trigger instead of `pull_request`. This
  gives pull requests access to the ambient OIDC credentials required to run
  `sigstore-conformance`. The workflow trigger section of the configuration
  should look like this:
```yaml
on:
  pull_request_target:
    types: [labeled]
```
- Create a pull request label called "safe to test". To mitigate the risk of
  third-party pull requests misusing these credentials, this action will only
  execute if the pull request has been vetted by a maintainer with write
  privileges and tagged with this label.
- In your GitHub repository settings, set "Fork pull request workflows from
  outside collaborators" to "Require approval for all outside collaborators"
  (the default setting is to require approval for first-time collaborators).
  This is not strictly required for the action to function, however we strongly
  recommend enabling this setting as an extra safeguard to prevent the ambient
  OIDC credentials from being misused.

## Licensing

`sigstore-conformance` is licensed under the Apache 2.0 License.

## Code of Conduct

Everyone interacting with this project is expected to follow the
[sigstore Code of Conduct](https://github.com/sigstore/.github/blob/main/CODE_OF_CONDUCT.md)

## Security

Should you discover any security issues, please refer to sigstore's [security
process](https://github.com/sigstore/.github/blob/main/SECURITY.md).
