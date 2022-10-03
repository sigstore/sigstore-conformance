import itertools

import pytest

from .matrix import ReleaseChannelChoice, SigstoreClientChoice

_clients = pytest.mark.parametrize("client", [c for c in SigstoreClientChoice])
_channels = pytest.mark.parametrize("channel", [c for c in ReleaseChannelChoice])


def _each_impl():
    for client in SigstoreClientChoice:
        for channel in ReleaseChannelChoice:
            yield (client, channel)


def conformance(func):
    return _clients(_channels(func))


def conformance_matrix(func):
    impls = itertools.combinations(_each_impl(), 2)
    return pytest.mark.parametrize("impls", impls)(func)
