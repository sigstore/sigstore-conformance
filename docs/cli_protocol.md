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

To simplify argument parsing, arguments will **always** be supplied by the
conformance suite in the order that they are specified in the templates below.

### Sign

#### Bundle flow

```console
${ENTRYPOINT} sign-bundle [--staging] [--in-toto] --identity-token TOKEN --bundle FILE FILE
```

| Option | Description |
| --- | --- |
| `--staging`        | Presence indicates client should use Sigstore staging infrastructure |
| `--in-toto`        | Presence indicates client should treat input file as an in-toto statement |
| `--identity-token` | The OIDC identity token to use |
| `--bundle FILE` | The path to write the bundle to |
| `--trusted-root TRUSTROOT` | Optional path to a custom trusted root to use to verify the bundle |
| `--signing-config SIGNINGCONFIG` | Optional path to a custom signing config to use when signing |
| `FILE` | The artifact to sign |

### Verify

#### Bundle flow

```console
${ENTRYPOINT} verify-bundle [--staging] --bundle FILE --certificate-identity IDENTITY --certificate-oidc-issuer URL [--trusted-root FILE] FILE_OR_DIGEST

${ENTRYPOINT} verify-bundle [--staging] --bundle FILE --key PATH_TO_KEY [--trusted-root FILE] FILE_OR_DIGEST
```

| Option | Description |
| --- | --- |
| `--staging`        | Presence indicates client should use Sigstore staging infrastructure |
| `--bundle FILE` | The path to the Sigstore bundle to verify |
| `--certificate-identity IDENTITY` | The expected identity in the signing certificate's SAN extension (not used when verifying with `--key`) |
| `--certificate-oidc-issuer URL` | The expected OIDC issuer for the signing certificate (not used when verifying with `--key`) |
| `--key PATH_TO_KEY` | The path to the PEM-encoded public key file (not used when verifying with `--certificate-identity`) |
| `--trusted-root TRUSTROOT` | Optional path to a custom trusted root to use to verify the bundle |
| `FILE_OR_DIGEST` | The path to the artifact to verify, or its digest. The digest should start with the `sha256:` prefix, should be the right length for a hexadecimal SHA-256 digest, and should not be a path on disk. If any of those conditions are not met, the input should be interpreted as a filepath instead. When the bundle contains a DSSE envelope with an in-toto statement, the input is a subject in the in-toto statement. |
