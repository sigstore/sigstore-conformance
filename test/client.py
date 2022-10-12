import os
import subprocess


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

        `entrypoint` is the entrypoint for the Sigstore client.
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
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        """
        Sign an artifact with the Sigstore client.

        `artifact` is a path to the file to sign.
        `certificate` is the path to write the signing certificate to.
        `signature` is the path to write the generated signature to.
        """
        self.run(
            "sign", "--certificate", certificate, "--signature", signature, artifact
        )

    def verify(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        """
        Verify an artifact with the Sigstore client.

        `artifact` is the path to the file to verify.
        `certificate` is the path to the signing certificate to verify with.
        `signature` is the path to the signature to verify.
        """
        self.run(
            "verify", "--certificate", certificate, "--signature", signature, artifact
        )
