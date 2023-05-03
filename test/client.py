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

    The `sign` and `verify` methods are dispatched over the two flows that clients
    should support: signature/certificate and bundle. The overloads of those
    methods should not be called directly.
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
        Sign an artifact with the Sigstore client. Dispatches to `_sign_for_sigcrt`
        when given `SignatureCertificateMaterials`, or `_sign_for_bundle` when given
        `BundleMaterials`.

        `artifact` is a path to the file to sign.
        `materials` contains paths to write the generated materials to.
        """

        raise NotImplementedError(f"Cannot sign with {type(materials)}")

    @sign.register
    def _sign_for_sigcrt(
        self, materials: SignatureCertificateMaterials, artifact: os.PathLike
    ) -> None:
        """
        Sign an artifact with the Sigstore client, producing a signature and certificate.

        This is an overload of `sign` for the signature/certificate flow and should not
        be called directly.
        """

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
    def _sign_for_bundle(self, materials: BundleMaterials, artifact: os.PathLike) -> None:
        """
        Sign an artifact with the Sigstore client, producing a bundle.

        This is an overload of `sign` for the bundle flow and should not be called directly.
        """

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
        Verify an artifact with the Sigstore client. Dispatches to `_verify_for_sigcrt`
        when given `SignatureCertificateMaterials`, or `_verify_for_bundle` when given
        `BundleMaterials`.

        `artifact` is the path to the file to verify.
        `materials` contains paths to the materials to verify with.
        """

        raise NotImplementedError(f"Cannot verify with {type(materials)}")

    @verify.register
    def _verify_for_sigcrt(
        self,
        materials: SignatureCertificateMaterials,
        artifact: os.PathLike,
    ) -> None:
        """
        Verify an artifact given a signature and certificate with the Sigstore client.

        This is an overload of `verify` for the signature/certificate flow and should
        not be called directly.
        """

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
    def _verify_for_bundle(self, materials: BundleMaterials, artifact: os.PathLike) -> None:
        """
        Verify an artifact given a bundle with the Sigstore client.

        This is an overload of `verify` for the bundle flow and should not be called
        directly.
        """

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
