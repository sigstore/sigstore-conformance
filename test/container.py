import os

import docker

from .matrix import ReleaseChannelChoice, SigstoreClientChoice

_WORKSPACE_VOLUME = "/mnt/volume"


class Container:
    """
    A wrapper around the Docker API to represent a container.
    """

    def __init__(
        self, client: SigstoreClientChoice, channel: ReleaseChannelChoice
    ) -> None:
        """
        Create a new `Container` for the given sigstore client and release channel permutation.
        """
        self.client = client
        self.channel = channel
        self.docker_client = docker.from_env()
        self.tag = (
            f"ghcr.io/trailofbits/sigstore-conformance/{self.client}:{self.channel}"
        )
        self.environment = {
            "GITHUB_ACTIONS": os.getenv("GITHUB_ACTIONS"),
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": os.getenv(
                "ACTIONS_ID_TOKEN_REQUEST_TOKEN"
            ),
            "ACTIONS_ID_TOKEN_REQUEST_URL": os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL"),
        }
        if self.client == SigstoreClientChoice.Cosign:
            self.environment["COSIGN_EXPERIMENTAL"] = "1"

    def run(self, cmd: str) -> None:
        """
        Execute a command in the container.

        The name of the client binary should NOT be included as this is the container entrypoint.
        For example, to execute the following command in the container:

        ```
        sigstore-python sign artifact.txt
        ```

        You should call the method like this:

        ```
        container.run("sign artifact.txt")
        ```
        """
        self.docker_client.containers.run(
            self.tag,
            cmd,
            volumes={
                os.getcwd(): {
                    "bind": _WORKSPACE_VOLUME,
                    "mode": "rw",
                }
            },
            environment=self.environment,
            working_dir=_WORKSPACE_VOLUME,
        )
