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


# ---------------------------------------------------------------------------
# Tests para formato v2 (con firma digital)
# ---------------------------------------------------------------------------


def test_recolectar_metadatos_con_signer():
    builder = VaultBuilder()
    aad = builder.recolectar_metadatos(
        "test.txt",
        [{"id": "bob", "encrypted_key": "123"}],
        signer_id="alice",
        signer_fingerprint="abcdef1234567890" * 4,
    )
    parsed = json.loads(aad.decode("utf-8"))

    assert parsed["version"] == "2.0.0"
    assert parsed["signer"]["id"] == "alice"
    assert parsed["signer"]["fingerprint"] == "abcdef1234567890" * 4


def test_recolectar_metadatos_sin_signer_es_v1():
    builder = VaultBuilder()
    aad = builder.recolectar_metadatos(
        "test.txt", [{"id": "bob", "encrypted_key": "123"}]
    )
    parsed = json.loads(aad.decode("utf-8"))

    assert parsed["version"] == "1.0.0"
    assert "signer" not in parsed


def test_empaquetar_desempaquetar_v2():
    builder = VaultBuilder()
    nonce = b"123456789012"
    aad = b'{"test":"v2"}'
    cipher = b"ciphertext_data_and_mac"
    signature = b"\xaa" * 64

    vault = builder.empaquetar(nonce, aad, cipher, signature=signature)

    assert vault[:8] == b"VAULT20\x00"

    out_nonce, out_aad, out_cipher, out_sig = builder.desempaquetar(vault)

    assert out_nonce == nonce
    assert out_aad == aad
    assert out_cipher == cipher
    assert out_sig == signature


def test_v1_sin_firma_sigue_funcionando():
    builder = VaultBuilder()
    nonce = b"123456789012"
    aad = b'{"test":"v1"}'
    cipher = b"ciphertext_data_and_mac"

    vault = builder.empaquetar(nonce, aad, cipher)

    assert vault[:8] == b"VAULT10\x00"

    result = builder.desempaquetar(vault)
    assert len(result) == 3

    out_nonce, out_aad, out_cipher = result
    assert out_nonce == nonce
    assert out_aad == aad
    assert out_cipher == cipher


def test_v2_con_ciphertext_grande():
    builder = VaultBuilder()
    nonce = b"123456789012"
    aad = b'{"file":"big.dat"}'
    cipher = b"\xff" * (1024 * 100)  # 100 KB
    signature = b"\xbb" * 64

    vault = builder.empaquetar(nonce, aad, cipher, signature=signature)
    out_nonce, out_aad, out_cipher, out_sig = builder.desempaquetar(vault)

    assert out_cipher == cipher
    assert out_sig == signature


def test_v2_header_distinto_de_v1():
    builder = VaultBuilder()
    nonce = b"123456789012"
    aad = b'{"test":"test"}'
    cipher = b"data"

    vault_v1 = builder.empaquetar(nonce, aad, cipher)
    vault_v2 = builder.empaquetar(nonce, aad, cipher, signature=b"\x00" * 64)

    assert vault_v1[:8] != vault_v2[:8]
    assert vault_v1[:8] == b"VAULT10\x00"
    assert vault_v2[:8] == b"VAULT20\x00"
