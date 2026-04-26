import pytest
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from secure_document_vault.core.facade import encriptar, desencriptar
from secure_document_vault.core.exceptions import IntegrityErrorException


# Helper para crear usuarios rapidamente
def create_user(user_id):
    x_priv = x25519.X25519PrivateKey.generate()
    e_priv = ed25519.Ed25519PrivateKey.generate()
    return {
        "id": user_id,
        "private_key": x_priv,
        "public_key": x_priv.public_key(),
        "signing_private_key": e_priv,
        "signing_public_key": e_priv.public_key(),
    }


# ESCENARIO 1: File shared with 2 users then both can decrypt.
def test_encrypt_decrypt_success():
    alice = create_user("alice")
    bob = create_user("bob")
    recipients = [alice, bob]

    nombre_archivo = "archivo.txt"
    plaintext = b"Mensaje secreto de prueba"

    vault = encriptar(plaintext, nombre_archivo, recipients, alice["id"], alice["signing_private_key"])

    # Alice should be able to decrypt
    recovered_alice = desencriptar(vault, "alice", alice["private_key"], alice["signing_public_key"])
    assert recovered_alice == plaintext

    # Bob should be able to decrypt
    recovered_bob = desencriptar(vault, "bob", bob["private_key"], alice["signing_public_key"])
    assert recovered_bob == plaintext


# ESCENARIO 2: Unauthorized user cannot decrypt.
def test_unauthorized_user():
    alice = create_user("alice")
    eve = create_user("eve")

    plaintext = b"Secreto de Alice"
    vault = encriptar(plaintext, "doc.txt", [alice], alice["id"], alice["signing_private_key"])

    with pytest.raises(IntegrityErrorException, match="no autorizado"):
        desencriptar(vault, "eve", eve["private_key"], alice["signing_public_key"])


# ESCENARIO 3: Wrong private key then fails.
def test_wrong_private_key():
    alice = create_user("alice")
    fake_alice_key = x25519.X25519PrivateKey.generate()

    plaintext = b"Dato"
    vault = encriptar(plaintext, "doc.txt", [alice], alice["id"], alice["signing_private_key"])

    with pytest.raises(IntegrityErrorException, match="Error al descifrar"):
        desencriptar(vault, "alice", fake_alice_key, alice["signing_public_key"])


# ESCENARIO 4: Tampered recipient list then decryption fails.
def test_metadata_tampering():
    alice = create_user("alice")
    plaintext = b"Archivo confidencial"
    vault = encriptar(plaintext, "secreto.txt", [alice], alice["id"], alice["signing_private_key"])

    corrupted = bytearray(vault)
    # The AAD contains the JSON. Modifying a byte in the first 100 bytes
    # (after the 24-byte header) alters the AAD.
    # Let's flip a bit exactly at index 29 (inside the AAD JSON string).
    corrupted[29] ^= 1

    with pytest.raises(IntegrityErrorException):
        desencriptar(bytes(corrupted), "alice", alice["private_key"], alice["signing_public_key"])


# ESCENARIO 5: Detectar modificación en el ciphertext
def test_ciphertext_tampering():
    alice = create_user("alice")
    plaintext = b"Datos importantes"
    vault = encriptar(plaintext, "doc.txt", [alice], alice["id"], alice["signing_private_key"])

    corrupted = bytearray(vault)
    # Modify a byte at the very end (ciphertext / MAC tag area)
    corrupted[-5] ^= 1

    with pytest.raises(IntegrityErrorException):
        desencriptar(bytes(corrupted), "alice", alice["private_key"], alice["signing_public_key"])


# ESCENARIO 6: Verificar que el nonce es diferente en cada cifrado
def test_nonce_randomness():
    alice = create_user("alice")
    plaintext = b"Mismo mensaje"

    vault1 = encriptar(plaintext, "file.txt", [alice], alice["id"], alice["signing_private_key"])
    vault2 = encriptar(plaintext, "file.txt", [alice], alice["id"], alice["signing_private_key"])

    assert vault1 != vault2
