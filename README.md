sigstore-conformance
====================

<!--- @begin-badges@ --->
![CI](https://github.com/sigstore/sigstore-conformance/workflows/CI/badge.svg)
<!--- @end-badges@ --->

`sigstore-conformance` is a conformance testing suite for Sigstore clients.

## Supported clients

The following clients are supported by `sigstore-conformance`:

- [sigstore-python](https://github.com/sigstore/sigstore-python)
- [cosign](https://github.com/sigstore/cosign)

## Design

- The `sigstore-conformance` suite is implemented in Python and is built on top
  of the [pytest](https://github.com/pytest-dev/pytest) testing framework.
- Each Sigstore client is expected to expose a CLI and is accessed by the test
  suite through a Docker container.
- The test suite is specifically designed to be run on GitHub Actions and takes
  advantage of its ambient OpenID Connect credentials.

## Adding clients

1. Create a `Dockerfile` for the latest release of the client under
   `conformance/stable/<CLIENT>/`.
2. Create a `Dockerfile` for the latest commit of the client under
   `conformance/nightly/<CLIENT>/`.
3. Add the client name to the testing matrix at `.github/workflows/ci.yml` to
   ensure that the new images are built in CI.
4. Add a new subclass of `SigstoreClient` in `test/matrix.py` and implement each
   of the methods.
5. Add a new item to the `SigstoreClientChoice` enumeration and some code to
   instantiate the new `SigstoreClient` under `SigstoreClientChoice.to_client`.
6. If applicable, add new entries to `.github/dependabot.yml` to keep the stable
   and nightly versions of the new client up to date.

## Adding tests

Add a new file under `test/functional/` following the naming convention,
 `test_<NAME>.py`. This file can contain one or more test functions:

```python
def test_<NAME>(client: SigstoreClient, workspace: Path) -> None:
    ...
```

The test function MUST have both of these arguments:

- The `client` argument is required for the test to be run as part of the
  testing matrix and provides an interface to each Sigstore client's API.
- The `workspace` argument causes a temporary directory to be created and
  mounted to the client Docker container and provides its path. The files under
  `artifacts/` are accessible via the workspace directory.

## Licensing

`sigstore-conformance` is licensed under the Apache 2.0 License.

## Code of Conduct

Everyone interacting with this project is expected to follow the
[sigstore Code of Conduct](https://github.com/sigstore/.github/blob/main/CODE_OF_CONDUCT.md).

## Security

Should you discover any security issues, please refer to sigstore's [security
process](https://github.com/sigstore/.github/blob/main/SECURITY.md).
