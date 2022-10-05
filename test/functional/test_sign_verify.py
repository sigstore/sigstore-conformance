import os

from ..container import ClientReleaseContainer


def test_sign_verify(client: ClientReleaseContainer) -> None:
    """
    A basic test that signs and verifies this repository's README with a given
    sigstore client.
    """
    # Sign and verify the README
    client.sign("README.md")
    client.verify("README.md")

    # TODO(alex): Probably need some setup/teardown phase for each test where we
    # setup/cleanup a fresh directory.
    os.remove("README.md.crt")
    os.remove("README.md.sig")
