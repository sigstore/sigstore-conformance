import pytest

from .matrix import ReleaseChannelChoice, SigstoreClientChoice


def conformance(func):
    return pytest.mark.parametrize("client", [v for v in SigstoreClientChoice])(
        pytest.mark.parametrize("channel", [v for v in ReleaseChannelChoice])(func)
    )
