import itertools

from .matrix import ReleaseChannelChoice, SigstoreClientChoice

_ALL_IMPLS = list(itertools.product(SigstoreClientChoice, ReleaseChannelChoice))


def pytest_generate_tests(metafunc):
    if "impl_a" in metafunc.fixturenames and "impl_b" in metafunc.fixturenames:
        metafunc.parametrize(
            ["impl_a", "impl_b"], itertools.permutations(_ALL_IMPLS, 2)
        )
