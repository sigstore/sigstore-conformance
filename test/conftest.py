import itertools

from .container import ClientReleaseContainer
from .matrix import ReleaseChannelChoice, SigstoreClientChoice

_ALL_IMPLS = list(itertools.product(SigstoreClientChoice, ReleaseChannelChoice))


def pytest_generate_tests(metafunc):
    if "client" in metafunc.fixturenames:
        metafunc.parametrize(
            ["client"], map(lambda perm: (ClientReleaseContainer(*perm),), _ALL_IMPLS)
        )
