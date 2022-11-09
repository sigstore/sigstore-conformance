import os
import subprocess

CERTIFICATE_EMAIL = (
    os.environ["GITHUB_SERVER_URL"]
    + "/"
    + os.environ["GITHUB_REPOSITORY"]
    + "/.github/workflows/conformance.yml@"
    + os.environ["GITHUB_REF"]
)
CERTIFICATE_OIDC_ISSUER = "https://token.actions.githubusercontent.com"


class SigstoreClient:
    """
    A wrapper around the Sigstore client under test that provides helpers to
    access client functionality.

    The `sigstore-conformance` test suite expects that clients expose a CLI that
    adheres to the protocol outlined at `docs/cli_protocol.md`.
    """

    def __init__(self, entrypoint: str) -> None:
        """
        Create a new `SigstoreClient`.

        `entrypoint` is the command to invoke the Sigstore client.
        """
        self.entrypoint = entrypoint

    def run(self, *args) -> None:
        """
        Execute a command against the Sigstore client.
        """
        subprocess.run(
            [self.entrypoint, *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )

    def sign(
        self, artifact: os.PathLike, signature: os.PathLike, certificate: os.PathLike
    ) -> None:
        """
        Sign an artifact with the Sigstore client.

        `artifact` is a path to the file to sign.
        `signature` is the path to write the generated signature to.
        `certificate` is the path to write the signing certificate to.
        """
        self.run(
            "sign", "--signature", signature, "--certificate", certificate, artifact
        )

    def verify(
        self, artifact: os.PathLike, signature: os.PathLike, certificate: os.PathLike
    ) -> None:
        """
        Verify an artifact with the Sigstore client.

        `artifact` is the path to the file to verify.
        `signature` is the path to the signature to verify.
        `certificate` is the path to the signing certificate to verify with.
        """
        # The email and OIDC issuer cannot be specified by the test since they remain constant
        # across the GitHub Actions job.
        self.run(
            "verify",
            "--signature",
            signature,
            "--certificate",
            certificate,
            "--certificate-email",
            CERTIFICATE_EMAIL,
            "--certificate-oidc-issuer",
            CERTIFICATE_OIDC_ISSUER,
            artifact,
        )
