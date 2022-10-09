import enum
import os
from abc import ABC, abstractmethod
from builtins import ValueError
from collections.abc import Container


class SigstoreClient(ABC):
    @abstractmethod
    def sign(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def verify(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        raise NotImplementedError


class SigstoreClientChoice(str, enum.Enum):
    """
    The Sigstore client to test
    """

    SigstorePython = "sigstore-python"
    Cosign = "cosign"

    def __str__(self) -> str:
        return self.value

    def to_client(self, container: Container) -> SigstoreClient:
        if self == SigstoreClientChoice.SigstorePython:
            return SigstorePythonClient(container)
        elif self == SigstoreClientChoice.Cosign:
            return CosignClient(container)
        else:
            raise ValueError


class ReleaseChannelChoice(str, enum.Enum):
    """
    The release channel for a given client
    """

    Stable = "stable"
    Nightly = "nightly"

    def __str__(self) -> str:
        return self.value


class SigstorePythonClient(SigstoreClient):
    def __init__(self, container: Container) -> None:
        self.container = container

    def sign(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        self.container.run(
            f"sign --certificate {certificate} --signature {signature} {artifact}"
        )

    def verify(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        self.container.run(
            f"verify --certificate {certificate} --signature {signature} {artifact}"
        )


class CosignClient(SigstoreClient):
    def __init__(self, container: Container) -> None:
        self.container = container

    def sign(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        self.container.run(
            f"sign-blob --output-certificate {certificate} --output-signature {signature} "
            f"{artifact}"
        )

    def verify(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        self.container.run(
            f"verify-blob --cert {certificate} --signature {signature} {artifact}"
        )
