import os

import docker


def sign_verify(client: docker.DockerClient, tag: str) -> None:
    """
    A basic test that signs and verifies this repository's README with a given
    sigstore client.
    """

    # TODO(alex): Refactor this all into a helper API
    volumes_mapping = {
        os.getcwd(): {
            "bind": "/mnt/vol1",
            "mode": "rw",
        }
    }
    env_mapping = {
        "GITHUB_ACTIONS": os.getenv("GITHUB_ACTIONS", ""),
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN": os.getenv(
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN", ""
        ),
        "ACTIONS_ID_TOKEN_REQUEST_URL": os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL", ""),
    }

    # Sign and verify the README
    client.containers.run(
        tag,
        command="sign /mnt/vol1/README.md",
        volumes=volumes_mapping,
        environment=env_mapping,
    )

    client.containers.run(
        tag,
        command="verify /mnt/vol1/README.md",
        volumes=volumes_mapping,
        environment=env_mapping,
    )
