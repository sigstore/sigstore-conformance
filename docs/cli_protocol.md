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

#### Signature and certificate flow

```console
${ENTRYPOINT} sign [--staging] --identity-token TOKEN --signature FILE --certificate FILE FILE
```

| Option | Description |
| --- | --- |
| `--staging`        | Presence indicates client should use Sigstore staging infrastructure |
| `--identity-token` | The OIDC identity token to use |
| `--signature FILE` | The path to write the signature to |
| `--certificate FILE` | The path to write the signing certificate to |
| `FILE` | The artifact to sign |

#### Bundle flow

```console
${ENTRYPOINT} sign-bundle [--staging] --identity-token TOKEN --bundle FILE FILE
```

| Option | Description |
| --- | --- |
| `--staging`        | Presence indicates client should use Sigstore staging infrastructure |
| `--identity-token` | The OIDC identity token to use |
| `--bundle FILE` | The path to write the bundle to |
| `FILE` | The artifact to sign |

### Verify

#### Signature and certificate flow

```console
${ENTRYPOINT} verify [--staging] --signature FILE --certificate FILE --certificate-identity IDENTITY --certificate-oidc-issuer URL [--trusted-root FILE] FILE
```

| Option | Description |
| --- | --- |
| `--staging`        | Presence indicates client should use Sigstore staging infrastructure |
| `--signature FILE` | The path to the signature to verify |
| `--certificate FILE` | The path to the signing certificate to verify |
| `--certificate-identity IDENTITY` | The expected identity in the signing certificate's SAN extension |
| `--certificate-oidc-issuer URL` | The expected OIDC issuer for the signing certificate |
| `--trusted-root` | The path of the custom trusted root to use to verify the signature |
| `FILE` | The path to the artifact to verify |

#### Bundle flow

```console
${ENTRYPOINT} verify-bundle [--staging] --bundle FILE --certificate-identity IDENTITY --certificate-oidc-issuer URL [--trusted-root FILE] [--verify-digest] FILE_OR_DIGEST
```

| Option | Description |
| --- | --- |
| `--staging`        | Presence indicates client should use Sigstore staging infrastructure |
| `--bundle FILE` | The path to the Sigstore bundle to verify |
| `--certificate-identity IDENTITY` | The expected identity in the signing certificate's SAN extension |
| `--certificate-oidc-issuer URL` | The expected OIDC issuer for the signing certificate |
| `--trusted-root` | The path of the custom trusted root to use to verify the bundle |
| `--verify-digest` | Presence indicates client should interpret `FILE_OR_DIGEST` as a digest. |
| `FILE_OR_DIGEST` | The path to the artifact to verify, or its digest. The digest should start with the `sha256:` prefix. |
