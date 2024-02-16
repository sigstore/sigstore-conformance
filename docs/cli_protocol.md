Conformance CLI Protocol
========================

While all Sigstore clients share some core functionality, each of them have
their own unique features and idiosyncracies that make their command lines
incompatible with one another. `sigstore-conformance` aims to test this common
feature set.

As an example of incompatibilities between clients, [cosign's](https://github.com/sigstore/cosign)
`sign` subcommand is designed to sign Docker containers rather than arbitrary
files (this behaviour is accessed via cosign's `sign-blob` subcommand). This
makes sense for cosign's use case, however it does diverge from other Sigstore
clients such as [sigstore-python](https://github.com/sigstore/sigstore-python)
and [sigstore-js](https://github.com/sigstore/sigstore-js).

To resolve these differences, we've established a CLI protocol for the test
suite to uniformly communicate with clients under test. Since the client's CLI
is unlikely to conform to this protocol, it may be necessary to write a thin
wrapper that converts the options described in this document to those that the
client's native CLI accepts.

## Subcommands

This is the set of subcommands that the test CLI must support. Each subcommand
has a provided syntax and list of descriptions for each argument.

To simplify argument parsing, all arguments are required, except `--staging`, and will **always** be
supplied by the conformance suite in the order that they are specified in the
templates below.

All commands below are allowed to run against staging, adding the `--staging` in the command, for example:

```console
${ENTRYPOINT} sign --identity-token TOKEN --signature FILE --certificate FILE FILE --staging
```

### Sign

#### Signature and certificate flow

```console
${ENTRYPOINT} sign --identity-token TOKEN --signature FILE --certificate FILE FILE
```

| Option | Description |
| --- | --- |
| `--identity-token` | The OIDC identity token to use |
| `--signature FILE` | The path to write the signature to |
| `--certificate FILE` | The path to write the signing certificate to |
| `FILE` | The artifact to sign |

#### Bundle flow

```console
${ENTRYPOINT} sign-bundle --identity-token TOKEN --bundle FILE FILE
```

| Option | Description |
| --- | --- |
| `--identity-token` | The OIDC identity token to use |
| `--bundle FILE` | The path to write the bundle to |
| `FILE` | The artifact to sign |

### Verify

#### Signature and certificate flow

```console
${ENTRYPOINT} verify --signature FILE --certificate FILE --certificate-identity IDENTITY --certificate-oidc-issuer URL [--trusted-root FILE] FILE
```

| Option | Description |
| --- | --- |
| `--signature FILE` | The path to the signature to verify |
| `--certificate FILE` | The path to the signing certificate to verify |
| `--certificate-identity IDENTITY` | The expected identity in the signing certificate's SAN extension |
| `--certificate-oidc-issuer URL` | The expected OIDC issuer for the signing certificate |
| `--trusted-root` | The path of the custom trusted root to use to verify the signature |
| `FILE` | The path to the artifact to verify |

#### Bundle flow

```console
${ENTRYPOINT} verify-bundle --bundle FILE --certificate-identity IDENTITY --certificate-oidc-issuer URL [--trusted-root FILE] FILE
```

| Option | Description |
| --- | --- |
| `--bundle FILE` | The path to the Sigstore bundle to verify |
| `--certificate-identity IDENTITY` | The expected identity in the signing certificate's SAN extension |
| `--certificate-oidc-issuer URL` | The expected OIDC issuer for the signing certificate |
| `--trusted-root` | The path of the custom trusted root to use to verify the bundle |
| `FILE` | The path to the artifact to verify |
