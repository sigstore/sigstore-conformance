from __future__ import annotations

import hashlib
import json
import subprocess
from base64 import b64decode
from contextlib import contextmanager
from datetime import datetime
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
    def from_artifact_path(cls, input: Path) -> VerificationMaterials:
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
    artifact: Path
    statement: Path | None
    subject: Path | None
    key: Path
    identity: str
    issuer: str

    @classmethod
    def from_dir(cls, path: Path) -> BundleMaterials:
        """Load Verification materials from directory

        See test/assets/bundle-verify/README.md for documentation
        """
        mats = cls()
        mats.bundle = path / "bundle.sigstore.json"

        # use custom trust root if one is provided
        trusted_root_path = path / "trusted_root.json"
        if trusted_root_path.exists():
            mats.trusted_root = trusted_root_path

        # use managed key for verifying if one is provided
        key_path = path / "key.pub"
        if key_path.exists():
            mats.key = key_path

        # use identity/issuer if is provided
        issuer_path = path / "issuer"
        if issuer_path.exists():
            mats.issuer = issuer_path.read_text().strip()
        else:
            mats.issuer = CERTIFICATE_OIDC_ISSUER
        identity_path = path / "identity"
        if identity_path.exists():
            mats.identity = identity_path.read_text().strip()
        else:
            mats.identity = CERTIFICATE_IDENTITY

        # use custom artifact path if one is provided
        artifact_path = path / "artifact"
        if artifact_path.exists():
            mats.artifact = artifact_path
        else:
            mats.artifact = Path("bundle-verify", "a.txt")

        return mats

    @classmethod
    def from_artifact_path(cls, input: Path) -> BundleMaterials:
        mats = cls()
        mats.bundle = input.parent / f"{input.name}.sigstore.json"
        mats.artifact = input

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

        # Dig issuer and identity from the token
        try:
            payload = self.identity_token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            payload_json = json.loads(b64decode(payload))
            self.identity: str = payload_json["email"]
            self.issuer: str = payload_json["iss"]
            self.expiry = datetime.fromtimestamp(payload_json["exp"])
        except (IndexError, KeyError, ValueError) as e:
            raise RuntimeError("Test suite failed to parse OIDC token") from e

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
    def sign(self, materials: VerificationMaterials) -> None:
        """
        Sign an artifact with the Sigstore client. Dispatches to `_sign_for_bundle` when
        given `BundleMaterials`.

        Materials will be updated with the used signing identity/issuer to ensure that a
        verify() call afterwards gets the correct identity/issuer.

        `artifact` is a path to the file to sign.
        `materials` contains paths to write the generated materials to.
        """

        raise NotImplementedError(f"Cannot sign with {type(materials)}")

    @sign.register
    def _sign_for_bundle(self, materials: BundleMaterials) -> None:
        """
        Sign an artifact with the Sigstore client, producing a bundle.

        This is an overload of `sign` for the bundle flow and should not be called directly.
        """
        lifetime = int((self.expiry - datetime.now()).total_seconds())
        if lifetime < 0:
            raise RuntimeError(
                "Signing test infrastructure failure: Test OIDC token expired "
                f"{-lifetime} seconds ago"
            )

        args = ["sign-bundle"]
        if self.staging:
            args.append("--staging")

        statement = getattr(materials, "statement", None)
        if statement is not None:
            args.append("--in-toto")
            artifact_to_sign = statement
        else:
            artifact_to_sign = materials.artifact

        args.extend(
            [
                "--identity-token",
                self.identity_token,
                "--bundle",
                str(materials.bundle),
            ]
        )
        if getattr(materials, "trusted_root", None) is not None:
            args.extend(["--trusted-root", str(materials.trusted_root)])
        if getattr(materials, "signing_config", None) is not None:
            args.extend(["--signing-config", str(materials.signing_config)])

        self.run(*args, str(artifact_to_sign))

        # Set the used signing identity and issuer on verification materials:
        # This way a later verify() call will know what to expect
        materials.identity = self.identity
        materials.issuer = self.issuer

    @singledispatchmethod
    def verify(self, materials: VerificationMaterials) -> None:
        """
        Verify an artifact with the Sigstore client. Dispatches to
         `_verify_{artifact|digest}_for_bundle` when given `BundleMaterials`.

        `artifact` is the path to the file to verify, or its digest.
        `materials` contains paths to the materials to verify with.
        """

        raise NotImplementedError(f"Cannot verify with {type(materials)}")

    @singledispatchmethod
    def verify_digest(self, materials: VerificationMaterials) -> None:
        raise NotImplementedError(f"Cannot verify with {type(materials)}")

    @verify_digest.register
    def _verify_digest_for_bundle(self, materials: BundleMaterials) -> None:
        args = self.build_verify_args(materials, digest=True)
        self.run(*args)

    @verify.register
    def _verify_artifact_for_bundle(self, materials: BundleMaterials) -> None:
        """
        Verify an artifact given a bundle with the Sigstore client.

        This is an overload of `verify` for the bundle flow and should not be called
        directly.
        """
        args = self.build_verify_args(materials)
        self.run(*args)

    def build_verify_args(self, materials: BundleMaterials, digest: bool = False) -> list[str]:
        args = ["verify-bundle"]
        if self.staging:
            args.append("--staging")

        args.extend(["--bundle", str(materials.bundle)])

        if getattr(materials, "key", None) is not None:
            args.extend(["--key", str(materials.key)])
        else:
            args.extend(
                [
                    "--certificate-identity",
                    materials.identity,
                    "--certificate-oidc-issuer",
                    materials.issuer,
                ]
            )

        if getattr(materials, "trusted_root", None) is not None:
            args.extend(["--trusted-root", str(materials.trusted_root)])

        subject = getattr(materials, "subject", None)
        if subject is not None:
            artifact_to_verify = subject
        else:
            artifact_to_verify = materials.artifact

        if digest:
            artifact = artifact_to_verify.read_bytes()
            digest_str = f"sha256:{hashlib.sha256(artifact).hexdigest()}"
            args.append(digest_str)
        else:
            args.append(str(artifact_to_verify))

        return args
