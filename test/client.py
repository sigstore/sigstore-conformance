import os
import subprocess


class SigstoreClient:
    def __init__(self, entrypoint: str) -> None:
        self.entrypoint = entrypoint

    def run(self, *args) -> None:
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
        self.run(
            "sign", "--certificate", certificate, "--signature", signature, artifact
        )

    def verify(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        self.run(
            "verify", "--certificate", certificate, "--signature", signature, artifact
        )
