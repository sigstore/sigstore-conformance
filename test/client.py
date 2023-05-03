from __future__ import annotations

import os
import subprocess
from functools import singledispatchmethod
from pathlib import Path

CERTIFICATE_IDENTITY = (
    "https://github.com/sigstore-conformance/extremely-dangerous-public-oidc-beacon/.github/"
    "workflows/extremely-dangerous-oidc-beacon.yml@refs/heads/main"
)
CERTIFICATE_OIDC_ISSUER = "https://token.actions.githubusercontent.com"


class VerificationMaterials:
    """
    A wrapper around verification materials. Materials can be either bundles
    or signatures and certificates.
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

    @classmethod
    def from_input(cls, input: Path) -> BundleMaterials:
        mats = cls()
        mats.bundle = input.parent / f"{input.name}.sigstore"

        return mats

    def exists(self) -> bool:
        return self.bundle.exists()


class SignatureCertificateMaterials(VerificationMaterials):
    """
    Materials for commands that produce or consume signatures and certificates.
    """

    signature: Path
    certificate: Path

    @classmethod
    def from_input(cls, input: Path) -> SignatureCertificateMaterials:
        mats = cls()
        mats.signature = input.parent / f"{input.name}.sig"
        mats.certificate = input.parent / f"{input.name}.crt"

        return mats

    def exists(self) -> bool:
        return self.signature.exists() and self.certificate.exists()


class SigstoreClient:
    """
    A wrapper around the Sigstore client under test that provides helpers to
    access client functionality.

    The `sigstore-conformance` test suite expects that clients expose a CLI that
    adheres to the protocol outlined at `docs/cli_protocol.md`.
    """

    def __init__(self, entrypoint: str, identity_token: str) -> None:
        """
        Create a new `SigstoreClient`.

        `entrypoint` is the command to invoke the Sigstore client.
        """
        self.entrypoint = entrypoint
        self.identity_token = identity_token

    def run(self, *args) -> None:
        """
        Execute a command against the Sigstore client.
        """
        subprocess.run(
            [self.entrypoint, *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )

    @singledispatchmethod
    def sign(self, materials: VerificationMaterials, artifact: os.PathLike) -> None:
        """
        Sign an artifact with the Sigstore client.

        `artifact` is a path to the file to sign.
        `materials` contains paths to write the generated materials to.
        """

        raise NotImplementedError(f"Cannot sign with {type(materials)}")

    @sign.register
    def _(
        self, materials: SignatureCertificateMaterials, artifact: os.PathLike
    ) -> None:
        self.run(
            "sign",
            "--identity-token",
            self.identity_token,
            "--signature",
            materials.signature,
            "--certificate",
            materials.certificate,
            artifact,
        )

    @sign.register
    def _(self, materials: BundleMaterials, artifact: os.PathLike) -> None:
        self.run(
            "sign-bundle",
            "--identity-token",
            self.identity_token,
            "--bundle",
            materials.bundle,
            artifact,
        )

    @singledispatchmethod
    def verify(
        self,
        materials: VerificationMaterials,
        artifact: os.PathLike,
    ) -> None:
        """
        Verify an artifact with the Sigstore client.

        `artifact` is the path to the file to verify.
        `materials` contains paths to the materials to verify with.
        """

        raise NotImplementedError(f"Cannot verify with {type(materials)}")

    @verify.register
    def _(
        self,
        materials: SignatureCertificateMaterials,
        artifact: os.PathLike,
    ) -> None:
        # The identity and OIDC issuer cannot be specified by the test since they remain constant
        # across the GitHub Actions job.

        self.run(
            "verify",
            "--signature",
            materials.signature,
            "--certificate",
            materials.certificate,
            "--certificate-identity",
            CERTIFICATE_IDENTITY,
            "--certificate-oidc-issuer",
            CERTIFICATE_OIDC_ISSUER,
            artifact,
        )

    @verify.register
    def _(self, materials: BundleMaterials, artifact: os.PathLike) -> None:
        self.run(
            "verify-bundle",
            "--bundle",
            materials.bundle,
            "--certificate-identity",
            CERTIFICATE_IDENTITY,
            "--certificate-oidc-issuer",
            CERTIFICATE_OIDC_ISSUER,
            artifact,
        )
