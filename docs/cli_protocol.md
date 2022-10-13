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
has a provided syntax, high-level description of what the subcommand is expected
to do and descriptions of each argument.

To simplify argument parsing, all arguments are required and will **always** be
supplied by the conformance suite in the order that they are specified in the
templates below.

### Sign

This subcommand is used to sign an artifact. The client should:

1. Request an ephemeral signing certificate from the production Fulcio instance.
2. Verify the Signed Certificate Timestamp (SCT) of the signing certificate.
3. Sign the artifact with this signing certificate and produce a signature.
4. Upload this signature to the production Rekor instance.
5. Write the signature to the disk.
6. Write the signing certificate to the disk.

```console
${ENTRYPOINT} sign --signature FILE --certificate FILE FILE
```

| Option | Description |
| --- | --- |
| `--signature FILE` | The path to write the signature to |
| `--certificate FILE` | The path to write the signing certificate to |
| `FILE` | The artifact to sign |

### Verify

This subcommand is used to verify the signature for an artifact. The client
should:

1. Verify that the signing certificate was signed by the Fulcio root
   certificate.
2. Verify that the expected email is found in the signing certificate's SAN
   extension.
3. Verify that the expected OIDC issuer is found in the signing certificate's
   OIDC issuer extension.
4. Verify that the signature was signed by the signing certificate.
5. Verify that there is a log entry for the signature on the production Rekor
   instance.
6. Verify the Inclusion Proof in the Rekor log entry.
7. Verify the Signed Entry Timestamp (SET) of the Rekor log entry.
8. Verify that the signing certificate was valid at the time of signing.

```console
${ENTRYPOINT} verify --signature FILE --certificate FILE --certificate-email EMAIL --certificate-oidc-issuer URL FILE
```

| Option | Description |
| --- | --- |
| `--signature FILE` | The path to the signature to verify |
| `--certificate FILE` | The path to the signing certificate to verify |
| `--certificate-email EMAIL` | The expected email in the signing certificate's SAN extension |
| `--certificate-oidc-issuer URL` | The expected OIDC issuer for the signing certificate |
| `FILE` | The path to the artifact to verify |
