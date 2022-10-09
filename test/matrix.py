import enum
import os
from abc import ABC, abstractmethod
from builtins import ValueError
from collections.abc import Container


class SigstoreClient(ABC):
    """
    Represents an abstract sigstore client.
    """

    @abstractmethod
    def sign(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        """
        Sign an artifact with the sigstore client.

        `artifact` is a path to the file to sign.
        `certificate` is the path to write the signing certificate to.
        `signature` is the path to write the generated signature to.
        """
        raise NotImplementedError

    @abstractmethod
    def verify(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        """
        Verify an artifact with the sigstore client.

        `artifact` is the path to the file to verify.
        `certificate` is the path to the signing certificate to verify with.
        `signature` is the path to the signature to verify.
        """
        raise NotImplementedError


class SigstoreClientChoice(str, enum.Enum):
    """
    The Sigstore client to test.
    """

    SigstorePython = "sigstore-python"
    Cosign = "cosign"

    def __str__(self) -> str:
        return self.value

    def to_client(self, container: Container) -> SigstoreClient:
        """
        Construct a `SigstoreClient` for a given choice.
        """
        if self == SigstoreClientChoice.SigstorePython:
            return SigstorePythonClient(container)
        elif self == SigstoreClientChoice.Cosign:
            return CosignClient(container)
        else:
            raise ValueError


class ReleaseChannelChoice(str, enum.Enum):
    """
    The release channel for a given client.
    """

    Stable = "stable"
    Nightly = "nightly"

    def __str__(self) -> str:
        return self.value


class SigstorePythonClient(SigstoreClient):
    """
    A `SigstoreClient` implementation for the `sigstore-python` client.
    """

    def __init__(self, container: Container) -> None:
        self.container = container

    def sign(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        """
        See `SigstoreClient.sign`.
        """
        self.container.run(
            f"sign --certificate {certificate} --signature {signature} {artifact}"
        )

    def verify(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        """
        See `SigstoreClient.verify`.
        """
        self.container.run(
            f"verify --certificate {certificate} --signature {signature} {artifact}"
        )


class CosignClient(SigstoreClient):
    """
    A `SigstoreClient` implementation for the `cosign` client.
    """

    def __init__(self, container: Container) -> None:
        self.container = container

    def sign(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        """
        See `SigstoreClient.sign`.
        """
        self.container.run(
            f"sign-blob --output-certificate {certificate} --output-signature {signature} "
            f"{artifact}"
        )

    def verify(
        self, artifact: os.PathLike, certificate: os.PathLike, signature: os.PathLike
    ) -> None:
        """
        See `SigstoreClient.verify`.
        """
        self.container.run(
            f"verify-blob --cert {certificate} --signature {signature} {artifact}"
        )
