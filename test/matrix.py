import enum


class SigstoreClientChoice(str, enum.Enum):
    """
    The Sigstore client to test.
    """

    SigstorePython = "sigstore-python"
    Cosign = "cosign"

    def __str__(self) -> str:
        return self.value

    @property
    def sign_command(self) -> str:
        if self == self.SigstorePython:
            return "sign"
        elif self == self.Cosign:
            return "sign-blob"
        else:
            raise ValueError

    @property
    def verify_command(self) -> str:
        if self == self.SigstorePython:
            return "verify"
        elif self == self.Cosign:
            return "verify-blob"
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
