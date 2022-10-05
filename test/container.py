import os

import docker

from .matrix import ReleaseChannelChoice, SigstoreClientChoice

_VOLUME = "/mnt/volume"


class ClientReleaseContainer:
    def __init__(
        self, client: SigstoreClientChoice, channel: ReleaseChannelChoice
    ) -> None:
        self.client = client
        self.channel = channel
        self.docker_client = docker.from_env()
        self.tag = f"{self.client}_{self.channel}"
        self.volumes = {
            os.getcwd(): {
                "bind": _VOLUME,
                "mode": "rw",
            }
        }
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
        self.docker_client.containers.run(
            self.tag,
            cmd,
            volumes=self.volumes,
            environment=self.environment,
            working_dir=_VOLUME,
        )

    def sign(self, cmd: str) -> None:
        self.run(f"{self.client.sign_command} {cmd}")

    def verify(self, cmd: str) -> None:
        self.run(f"{self.client.verify_command} {cmd}")
