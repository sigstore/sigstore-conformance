from ..container import ClientReleaseContainer


def sign_verify(container: ClientReleaseContainer) -> None:
    """
    A basic test that signs and verifies this repository's README with a given
    sigstore client.
    """

    # Sign and verify the README
    container.run("sign README.md")
    container.run("verify README.md")
