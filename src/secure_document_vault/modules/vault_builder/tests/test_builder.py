import pytest
import json
from secure_document_vault.modules.vault_builder.builder import VaultBuilder


def test_recolectar_metadatos():
    builder = VaultBuilder()
    aad = builder.recolectar_metadatos(
        "test.txt", [{"id": "bob", "encrypted_key": "123"}]
    )
    parsed = json.loads(aad.decode("utf-8"))

    assert parsed["file_name"] == "test.txt"
    assert parsed["recipients"][0]["id"] == "bob"
    assert parsed["version"] == "1.0.0"


def test_empaquetar_desempaquetar():
    builder = VaultBuilder()
    nonce = b"123456789012"
    aad = b'{"test":"test"}'
    cipher = b"ciphertext_data_and_mac"

    vault = builder.empaquetar(nonce, aad, cipher)

    out_nonce, out_aad, out_cipher = builder.desempaquetar(vault)

    assert out_nonce == nonce
    assert out_aad == aad
    assert out_cipher == cipher


def test_desempaquetar_invalid_header():
    builder = VaultBuilder()
    bad_vault = b"BADHEAD\x00" + b"restofdata"

    with pytest.raises(ValueError, match="Header incorrecto"):
        builder.desempaquetar(bad_vault)
