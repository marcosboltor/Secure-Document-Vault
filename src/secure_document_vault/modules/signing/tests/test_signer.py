import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from secure_document_vault.modules.signing.signer import DocumentSigner


def test_generate_key_pair():
    priv, pub = DocumentSigner.generate_key_pair()

    assert isinstance(priv, Ed25519PrivateKey)
    assert isinstance(pub, Ed25519PublicKey)


def test_generate_key_pair_unique():
    _, pub1 = DocumentSigner.generate_key_pair()
    _, pub2 = DocumentSigner.generate_key_pair()

    assert pub1.public_bytes_raw() != pub2.public_bytes_raw()


def test_fingerprint_format():
    _, pub = DocumentSigner.generate_key_pair()
    fp = DocumentSigner.get_fingerprint(pub)

    assert isinstance(fp, str)
    assert len(fp) == 64  # SHA-256 hex = 64 chars
    assert all(c in "0123456789abcdef" for c in fp)


def test_fingerprint_deterministic():
    _, pub = DocumentSigner.generate_key_pair()

    fp1 = DocumentSigner.get_fingerprint(pub)
    fp2 = DocumentSigner.get_fingerprint(pub)

    assert fp1 == fp2


def test_fingerprint_unique_per_key():
    _, pub1 = DocumentSigner.generate_key_pair()
    _, pub2 = DocumentSigner.generate_key_pair()

    assert DocumentSigner.get_fingerprint(pub1) != DocumentSigner.get_fingerprint(pub2)


def test_sign_returns_64_bytes():
    priv, _ = DocumentSigner.generate_key_pair()
    data = b"test data"

    signature = DocumentSigner.sign(priv, data)

    assert isinstance(signature, bytes)
    assert len(signature) == 64


def test_sign_verify_valid():
    priv, pub = DocumentSigner.generate_key_pair()
    data = b"message to sign"

    signature = DocumentSigner.sign(priv, data)
    result = DocumentSigner.verify(pub, data, signature)

    assert result is True


def test_verify_tampered_data_rejected():
    priv, pub = DocumentSigner.generate_key_pair()
    data = b"original data"

    signature = DocumentSigner.sign(priv, data)

    with pytest.raises(InvalidSignature):
        DocumentSigner.verify(pub, b"tampered data", signature)


def test_verify_wrong_public_key_rejected():
    priv1, _ = DocumentSigner.generate_key_pair()
    _, pub2 = DocumentSigner.generate_key_pair()
    data = b"test data"

    signature = DocumentSigner.sign(priv1, data)

    with pytest.raises(InvalidSignature):
        DocumentSigner.verify(pub2, data, signature)


def test_verify_corrupted_signature_rejected():
    priv, pub = DocumentSigner.generate_key_pair()
    data = b"test data"

    signature = DocumentSigner.sign(priv, data)
    corrupted = bytearray(signature)
    corrupted[0] ^= 1

    with pytest.raises(Exception):
        DocumentSigner.verify(pub, data, bytes(corrupted))


def test_sign_empty_data():
    priv, pub = DocumentSigner.generate_key_pair()
    data = b""

    signature = DocumentSigner.sign(priv, data)
    result = DocumentSigner.verify(pub, data, signature)

    assert result is True


def test_sign_large_data():
    priv, pub = DocumentSigner.generate_key_pair()
    data = b"A" * (1024 * 1024)  # 1 MB

    signature = DocumentSigner.sign(priv, data)
    result = DocumentSigner.verify(pub, data, signature)

    assert result is True
    assert len(signature) == 64
