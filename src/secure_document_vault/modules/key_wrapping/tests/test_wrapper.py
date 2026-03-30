import pytest
import os
from cryptography.hazmat.primitives.asymmetric import x25519
from secure_document_vault.modules.key_wrapping.wrapper import ECCKeyWrapper


def test_wrap_unwrap_success():
    recipient_priv = x25519.X25519PrivateKey.generate()
    recipient_pub = recipient_priv.public_key()

    file_key = os.urandom(32)
    wrapped = ECCKeyWrapper.wrap_key(file_key, recipient_pub)

    assert "ephemeral_pub" in wrapped
    assert "nonce" in wrapped
    assert "encrypted_key" in wrapped

    unwrapped = ECCKeyWrapper.unwrap_key(wrapped, recipient_priv)
    assert file_key == unwrapped


def test_unwrap_wrong_key_fails():
    recipient_priv = x25519.X25519PrivateKey.generate()
    recipient_pub = recipient_priv.public_key()
    wrong_priv = x25519.X25519PrivateKey.generate()

    file_key = os.urandom(32)
    wrapped = ECCKeyWrapper.wrap_key(file_key, recipient_pub)

    with pytest.raises(Exception):
        ECCKeyWrapper.unwrap_key(wrapped, wrong_priv)
