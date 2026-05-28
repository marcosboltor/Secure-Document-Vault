import pytest
import os
from secure_document_vault.modules.aead.engine import AEAD_Engine
from secure_document_vault.core.exceptions import IntegrityErrorException


@pytest.fixture
def keys():
    return os.urandom(32), os.urandom(12)


def test_encrypt_decrypt(keys):
    key, nonce = keys
    engine = AEAD_Engine(key)
    plaintext = b"Test Message"
    aad = b"Metadata"

    ciphertext = engine.encrypt(nonce, plaintext, aad)
    decrypted = engine.decrypt(nonce, ciphertext, aad)
    assert decrypted == plaintext


def test_decrypt_invalid_tag(keys):
    key, nonce = keys
    engine = AEAD_Engine(key)
    plaintext = b"Test Message"
    aad = b"Metadata"

    ciphertext = engine.encrypt(nonce, plaintext, aad)

    # Modify ciphertext
    corrupted = bytearray(ciphertext)
    corrupted[-1] ^= 1

    with pytest.raises(IntegrityErrorException, match="ALERTA DE SEGURIDAD"):
        engine.decrypt(nonce, bytes(corrupted), aad)
