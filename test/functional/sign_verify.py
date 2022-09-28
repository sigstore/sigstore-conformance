from ..container import ClientReleaseContainer


def sign_verify(container: ClientReleaseContainer) -> None:
    """
    A basic test that signs and verifies this repository's README with a given
    sigstore client.
    """

    # Sign and verify the README
    if container.tag.startswith("cosign"):
        # TODO(alex): Figure out a better way to represent this. Maybe some kind
        # of ABC for each client that exposes a `sign` and `verify` property?
        container.run("sign-blob --overwrite README.md")
        container.run("verify-blob README.md")
    else:
        container.run("sign --overwrite README.md")
        container.run("verify README.md")
