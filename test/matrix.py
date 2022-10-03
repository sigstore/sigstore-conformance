import enum


class SigstoreClientChoice(str, enum.Enum):
    """
    The Sigstore client to test.
    """

    SigstorePython = "sigstore-python"
    Cosign = "cosign"

    def __str__(self) -> str:
        return self.value


class ReleaseChannelChoice(str, enum.Enum):
    """
    The release channel for a given client.
    """

    Stable = "stable"
    Nightly = "nightly"

    def __str__(self) -> str:
        return self.value
