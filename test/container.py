import os

import docker


class ClientReleaseContainer:
    def __init__(self, tag: str) -> None:
        self.docker_client = docker.from_env()
        self.tag = tag
        self.volumes = {
            os.getcwd(): {
                "bind": "/mnt/volume",
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

    def run(self, cmd: str) -> None:
        self.docker_client.containers.run(
            self.tag,
            cmd,
            volumes=self.volumes,
            environment=self.environment,
            working_dir="/mnt/volume",
        )
