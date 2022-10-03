import os

import pytest

from ..container import ClientReleaseContainer
from ..matrix import ReleaseChannelChoice, SigstoreClientChoice


@pytest.mark.parametrize("client", [v for v in SigstoreClientChoice])
@pytest.mark.parametrize("channel", [v for v in ReleaseChannelChoice])
def test_sign_verify(
    client: SigstoreClientChoice, channel: ReleaseChannelChoice
) -> None:
    """
    A basic test that signs and verifies this repository's README with a given
    sigstore client.
    """
    container = ClientReleaseContainer(f"{client}_{channel}")

    # Sign and verify the README
    if container.tag.startswith("cosign"):
        # TODO(alex): Figure out a better way to represent this. Maybe some kind
        # of ABC for each client that exposes a `sign` and `verify` property?
        container.run("sign-blob README.md")
        container.run("verify-blob README.md")
    else:
        container.run("sign README.md")
        container.run("verify README.md")

    # TODO(alex): Probably need some setup/teardown phase for each test where we
    # setup/cleanup a fresh directory.
    os.remove("README.md.crt")
    os.remove("README.md.sig")
