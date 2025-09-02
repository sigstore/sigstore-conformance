from __future__ import annotations

import os
import subprocess
from contextlib import contextmanager
from functools import singledispatchmethod
from pathlib import Path

CERTIFICATE_IDENTITY = (
    "https://github.com/sigstore-conformance/extremely-dangerous-public-oidc-beacon/.github/"
    "workflows/extremely-dangerous-oidc-beacon.yml@refs/heads/main"
)
CERTIFICATE_OIDC_ISSUER = "https://token.actions.githubusercontent.com"

_CLIENT_ERROR_MSG = """
Command: {command}
Exit code: {exitcode}

!!! STDOUT !!!
==============

{stdout}

!!! STDERR !!!
==============

{stderr}
"""


class ClientFail(Exception):
    pass


class ClientUnexpectedSuccess(Exception):
    pass


class VerificationMaterials:
    """
    A wrapper around verification materials. Materials are bundles.
    """

    @classmethod
    def from_input(cls, input: Path) -> VerificationMaterials:
        """
        Constructs a new set of materials from the given input path.
        """

        raise NotImplementedError

    def exists(self) -> bool:
        """
        Checks if all contained materials exist at specified paths.
        """

        raise NotImplementedError


class BundleMaterials(VerificationMaterials):
    """
    Materials for commands that produce or consume bundles.
    """

    bundle: Path
    trusted_root: Path
    signing_config: Path

    @classmethod
    def from_path(cls, bundle: Path) -> BundleMaterials:
        mats = cls()
        mats.bundle = bundle
        return mats

    @classmethod
    def from_input(cls, input: Path) -> BundleMaterials:
        mats = cls()
        mats.bundle = input.parent / f"{input.name}.sigstore.json"

        return mats

    def exists(self) -> bool:
        return self.bundle.exists()


class SigstoreClient:
    """
    A wrapper around the Sigstore client under test that provides helpers to
    access client functionality.

    The `sigstore-conformance` test suite expects that clients expose a CLI that
    adheres to the protocol outlined at `docs/cli_protocol.md`.

    The `sign` and `verify` methods are dispatched over the one flows that clients
    support: bundles. The overloads of those methods should not be called directly.
    """

    def __init__(self, entrypoint: str, identity_token: str, staging: bool) -> None:
        """
        Create a new `SigstoreClient`.

        `entrypoint` is the command to invoke the Sigstore client.
        """
        self.entrypoint = entrypoint
        self.identity_token = identity_token
        self.completed_process: subprocess.CompletedProcess | None = None
        self.staging = staging

    def run(self, *args) -> None:
        """
        Execute a command against the Sigstore client.
        """
        self.completed_process = None
        full_command = [self.entrypoint, *args]

        try:
            self.completed_process = subprocess.run(
                full_command,
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as cpe:
            msg = _CLIENT_ERROR_MSG.format(
                exitcode=cpe.returncode,
                command=" ".join(map(str, cpe.args)),
                stdout=cpe.stdout,
                stderr=cpe.stderr,
            )
            raise ClientFail(msg)

    @contextmanager
    def raises(self):
        try:
            yield
        except ClientFail:
            pass
        else:
            assert self.completed_process
            msg = _CLIENT_ERROR_MSG.format(
                exitcode=self.completed_process.returncode,
                command=" ".join(map(str, self.completed_process.args)),
                stdout=self.completed_process.stdout,
                stderr=self.completed_process.stderr,
            )
            raise ClientUnexpectedSuccess(msg)

    @singledispatchmethod
    def sign(self, materials: VerificationMaterials, artifact: os.PathLike) -> None:
        """
        Sign an artifact with the Sigstore client. Dispatches to `_sign_for_bundle` when
        given `BundleMaterials`.

        `artifact` is a path to the file to sign.
        `materials` contains paths to write the generated materials to.
        """

        raise NotImplementedError(f"Cannot sign with {type(materials)}")

    @sign.register
    def _sign_for_bundle(self, materials: BundleMaterials, artifact: os.PathLike) -> None:
        """
        Sign an artifact with the Sigstore client, producing a bundle.

        This is an overload of `sign` for the bundle flow and should not be called directly.
        """

        args: list[str | os.PathLike] = ["sign-bundle"]
        if self.staging:
            args.append("--staging")
        args.extend(
            [
                "--identity-token",
                self.identity_token,
                "--bundle",
                materials.bundle,
            ]
        )
        if getattr(materials, "trusted_root", None) is not None:
            args.extend(["--trusted-root", materials.trusted_root])
        if getattr(materials, "signing_config", None) is not None:
            args.extend(["--signing-config", materials.signing_config])

        self.run(*args, artifact)

    @singledispatchmethod
    def verify(self, materials: VerificationMaterials, artifact: os.PathLike | str) -> None:
        """
        Verify an artifact with the Sigstore client. Dispatches to
         `_verify_{artifact|digest}_for_bundle` when given `BundleMaterials`.

        `artifact` is the path to the file to verify, or its digest.
        `materials` contains paths to the materials to verify with.
        """

        raise NotImplementedError(f"Cannot verify with {type(materials)}")

    @verify.register
    def _verify_artifact_for_bundle(
        self, materials: BundleMaterials, artifact: os.PathLike
    ) -> None:
        """
        Verify an artifact given a bundle with the Sigstore client.

        This is an overload of `verify` for the bundle flow and should not be called
        directly.
        """
        args: list[str | os.PathLike] = ["verify-bundle"]
        if self.staging:
            args.append("--staging")
        args.extend(
            [
                "--bundle",
                materials.bundle,
                "--certificate-identity",
                CERTIFICATE_IDENTITY,
                "--certificate-oidc-issuer",
                CERTIFICATE_OIDC_ISSUER,
            ]
        )

        if getattr(materials, "trusted_root", None) is not None:
            args.extend(["--trusted-root", materials.trusted_root])

        self.run(*args, artifact)

    @verify.register
    def _verify_digest_for_bundle(self, materials: BundleMaterials, digest: str) -> None:
        """
        Verify a digest given a bundle with the Sigstore client.

        This is an overload of `verify` for the bundle flow and should not be called
        directly. The digest string is expected to start with the `sha256:` prefix.
        """
        args: list[str | os.PathLike] = ["verify-bundle"]
        if self.staging:
            args.append("--staging")
        args.extend(
            [
                "--bundle",
                materials.bundle,
                "--certificate-identity",
                CERTIFICATE_IDENTITY,
                "--certificate-oidc-issuer",
                CERTIFICATE_OIDC_ISSUER,
            ]
        )

        if getattr(materials, "trusted_root", None) is not None:
            args.extend(["--trusted-root", materials.trusted_root])

        self.run(*args, digest)
