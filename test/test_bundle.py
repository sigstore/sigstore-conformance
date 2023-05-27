from subprocess import CalledProcessError
from test.client import BundleMaterials, SigstoreClient
from test.conftest import _MakeMaterialsByType

import pytest  # type: ignore
from cryptography import x509
from sigstore_protobuf_specs.dev.sigstore.bundle.v1 import Bundle


def test_verify_rejects_root(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client rejects a bundle that contains a root certificate.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type(
        "has_root_in_chain.txt", BundleMaterials
    )

    with pytest.raises(CalledProcessError):
        client.verify(materials, input_path)


def test_sign_does_not_produce_root(
    client: SigstoreClient, make_materials_by_type: _MakeMaterialsByType
) -> None:
    """
    Check that the client does not produce a bundle that contains a root
    certificate.
    """

    materials: BundleMaterials
    input_path, materials = make_materials_by_type("a.txt", BundleMaterials)
    assert not materials.exists()

    # Sign for our input.
    client.sign(materials, input_path)

    # Parse the output bundle.
    bundle_contents = materials.bundle.read_bytes()
    bundle = Bundle().from_json(bundle_contents)

    # Iterate over our cert chain and check for roots.
    certs = bundle.verification_material.x509_certificate_chain
    for cert in certs.certificates:
        cert = x509.load_der_x509_certificate(cert.raw_bytes)

        try:
            constraints = cert.extensions.get_extension_for_class(x509.BasicConstraints)
            assert not constraints.value.ca
        # BasicConstraints isn't required to appear in leaf certificates.
        except x509.ExtensionNotFound:
            pass
