import os

from ..container import ClientReleaseContainer


def test_sign_verify(client: ClientReleaseContainer) -> None:
    """
    A basic test that signs and verifies this repository's README with a given
    sigstore client.
    """
    # Sign and verify the README
    client.sign("--output-certificate README.md.crt --output-signature README.md.sig README.md")
    client.verify("--cert README.md.crt --signature README.md.sig README.md")

    # TODO(alex): Probably need some setup/teardown phase for each test where we
    # setup/cleanup a fresh directory.
    os.remove("README.md.crt")
    os.remove("README.md.sig")