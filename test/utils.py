import pytest

from .matrix import ReleaseChannelChoice, SigstoreClientChoice

_clients = pytest.mark.parametrize("client", [c for c in SigstoreClientChoice])
_channels = pytest.mark.parametrize("channel", [c for c in ReleaseChannelChoice])


def _each_impl():
    for client in SigstoreClientChoice:
        for channel in ReleaseChannelChoice:
            yield (client, channel)


def _impls(name):
    return pytest.mark.parametrize(name, _each_impl())


def conformance(func):
    return _clients(_channels(func))


def conformance_matrix(func):
    return _impls("impl_a")(_impls("impl_b")(func))
