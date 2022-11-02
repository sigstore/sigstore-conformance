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

To simplify argument parsing, all arguments are required and will **always** be
supplied by the conformance suite in the order that they are specified in the
templates below.

### Sign

```console
${ENTRYPOINT} sign --signature FILE --certificate FILE FILE
```

| Option | Description |
| --- | --- |
| `--signature FILE` | The path to write the signature to |
| `--certificate FILE` | The path to write the signing certificate to |
| `FILE` | The artifact to sign |

### Verify

```console
${ENTRYPOINT} verify --signature FILE --certificate FILE --certificate-oidc-issuer URL FILE
```

| Option | Description |
| --- | --- |
| `--signature FILE` | The path to the signature to verify |
| `--certificate FILE` | The path to the signing certificate to verify |
| `--certificate-oidc-issuer URL` | The expected OIDC issuer for the signing certificate |
| `FILE` | The path to the artifact to verify |
