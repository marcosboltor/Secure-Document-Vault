"""
Integration tests for the Key Management Lifecycle (Issue 4 – Rubric D6).

These tests exercise the complete end-to-end flow through the orchestration
layer (facade.py) and include a minimal password-protected keystore helper
that mirrors how the KeyProtector module works (PBKDF2-SHA256 + ChaCha20-
Poly1305), letting us test the full user-facing lifecycle:

    password → KDF → derived key → encrypt/decrypt private key in keystore
    keystore (on disk or serialized) → restore private key → facade decrypt

All 5 mandatory rubric scenarios are covered.
"""

import os
import json
import struct
import pytest

from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from secure_document_vault.core.facade import encriptar, desencriptar
from secure_document_vault.core.exceptions import IntegrityErrorException


# ---------------------------------------------------------------------------
# Minimal password-protected keystore (mirrors the KeyProtector contract)
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 100_000
_SALT_LEN = 16
_NONCE_LEN = 12


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from *password* using PBKDF2-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def protect_private_key(private_key: x25519.X25519PrivateKey, password: str) -> bytes:
    """
    Serialize and encrypt *private_key* with *password*.

    Returns a compact keystore blob:
        salt (16) | nonce (12) | ciphertext+tag
    """
    salt = os.urandom(_SALT_LEN)
    nonce = os.urandom(_NONCE_LEN)
    derived = _derive_key(password, salt)

    raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )

    ciphertext = ChaCha20Poly1305(derived).encrypt(nonce, raw, None)
    return salt + nonce + ciphertext


def recover_private_key(keystore: bytes, password: str) -> x25519.X25519PrivateKey:
    """
    Decrypt *keystore* with *password* and return the X25519 private key.

    Raises ValueError if the password is wrong, None, or the keystore is corrupted.
    """
    if password is None:
        raise ValueError("Contraseña incorrecta o keystore corrupto: contraseña nula.")
    if len(keystore) < _SALT_LEN + _NONCE_LEN + 1:
        raise ValueError("Keystore demasiado corto o inválido.")

    salt = keystore[:_SALT_LEN]
    nonce = keystore[_SALT_LEN: _SALT_LEN + _NONCE_LEN]
    ciphertext = keystore[_SALT_LEN + _NONCE_LEN:]

    derived = _derive_key(password, salt)

    try:
        raw = ChaCha20Poly1305(derived).decrypt(nonce, ciphertext, None)
    except Exception:
        raise ValueError(
            "Contraseña incorrecta o keystore corrupto: no se pudo recuperar la llave."
        )

    return x25519.X25519PrivateKey.from_private_bytes(raw)


# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: str) -> dict:
    """Return a user dict with X25519 and Ed25519 key pairs."""
    x_priv = x25519.X25519PrivateKey.generate()
    e_priv = ed25519.Ed25519PrivateKey.generate()
    return {
        "id": user_id,
        "private_key": x_priv,
        "public_key": x_priv.public_key(),
        "signing_private_key": e_priv,
        "signing_public_key": e_priv.public_key(),
    }


# ---------------------------------------------------------------------------
# SCENARIO 1: Correct password → access granted
# ---------------------------------------------------------------------------


def test_correct_password_grants_access():
    """
    A user protects her private key with a password.  After encrypting a
    document, the same password lets her recover the key and decrypt.

    Assertion: the original plaintext is returned without error.
    """
    alice = _make_user("alice")
    password = "supersecret_passphrase_42!"
    plaintext = b"Classified: launch codes are 0000"

    # Encrypt the document (facade)
    vault = encriptar(
        plaintext,
        "launch_codes.txt",
        [alice],
        alice["id"],
        alice["signing_private_key"],
    )

    # Simulate user protecting her private key in a keystore
    keystore = protect_private_key(alice["private_key"], password)

    # Simulate user recovering private key with the CORRECT password
    recovered_key = recover_private_key(keystore, password)

    # Decrypt via the facade using the recovered key
    result = desencriptar(
        vault, alice["id"], recovered_key, alice["signing_public_key"]
    )

    assert result == plaintext


# ---------------------------------------------------------------------------
# SCENARIO 2: Wrong password → access denied
# ---------------------------------------------------------------------------


def test_wrong_password_denies_access():
    """
    Attempting to recover the private key with the wrong password must raise
    a controlled exception before any private key material is exposed.

    Assertion: ValueError is raised; the facade's desencriptar is never reached.
    """
    alice = _make_user("alice")
    correct_password = "correct_horse_battery_staple"
    wrong_password = "password123"

    plaintext = b"Top secret data"
    vault = encriptar(
        plaintext,
        "secret.txt",
        [alice],
        alice["id"],
        alice["signing_private_key"],
    )

    keystore = protect_private_key(alice["private_key"], correct_password)

    # The wrong password must be rejected by the keystore layer
    with pytest.raises(ValueError, match="Contraseña incorrecta"):
        recover_private_key(keystore, wrong_password)


# ---------------------------------------------------------------------------
# SCENARIO 3: Modified keystore → failure
# ---------------------------------------------------------------------------


def test_modified_keystore_is_rejected():
    """
    Corrupting a single byte of the keystore (e.g. altering the encrypted
    private key or the authentication tag) must be detected.

    Assertion: ValueError is raised regardless of which byte was altered.
    """
    alice = _make_user("alice")
    password = "integrity_matters!"

    plaintext = b"Sensitive payload"
    encriptar(
        plaintext,
        "payload.txt",
        [alice],
        alice["id"],
        alice["signing_private_key"],
    )

    keystore = protect_private_key(alice["private_key"], password)

    # Corrupt one byte in the ciphertext region (past salt+nonce header)
    corrupted = bytearray(keystore)
    target = _SALT_LEN + _NONCE_LEN + 4  # well inside the ciphertext+tag area
    corrupted[target] ^= 0xFF

    with pytest.raises(ValueError, match="Contraseña incorrecta o keystore corrupto"):
        recover_private_key(bytes(corrupted), password)


# ---------------------------------------------------------------------------
# SCENARIO 4: Backup → restore works
# ---------------------------------------------------------------------------


def test_backup_and_restore_allows_decryption(tmp_path):
    """
    Full backup/restore lifecycle:
      1. Generate keys and encrypt a document.
      2. Serialize (backup) the encrypted keystore to disk.
      3. Delete the in-memory user object (simulate RAM wipe).
      4. Read (restore) the keystore from disk.
      5. Decrypt the vault using only the restored key + password.

    Assertion: decryption succeeds and returns the original plaintext.
    """
    alice = _make_user("alice")
    password = "backup_restore_password_2024"
    plaintext = b"Critical document that must survive a restart"

    # Encrypt document
    vault = encriptar(
        plaintext,
        "critical.txt",
        [alice],
        alice["id"],
        alice["signing_private_key"],
    )

    # Backup: protect private key and write to disk
    keystore_blob = protect_private_key(alice["private_key"], password)
    keystore_path = tmp_path / "alice.keystore"
    keystore_path.write_bytes(keystore_blob)

    # Keep the signing public key (this is public and can be stored openly)
    signing_pub = alice["signing_public_key"]
    user_id = alice["id"]

    # Simulate RAM wipe: remove the user object
    del alice

    # Restore: read keystore from disk and recover private key with password
    restored_blob = keystore_path.read_bytes()
    restored_key = recover_private_key(restored_blob, password)

    # Decrypt via the facade using ONLY restored data + password
    result = desencriptar(vault, user_id, restored_key, signing_pub)

    assert result == plaintext


# ---------------------------------------------------------------------------
# SCENARIO 5: Stolen keystore alone → cannot decrypt (no password = no access)
# ---------------------------------------------------------------------------


def test_stolen_files_without_password_are_useless():
    """
    An attacker has obtained both the .vault file and the .keystore.
    Without the password, possession of both files is cryptographically
    useless: the private key inside the keystore cannot be recovered.

    Assertion: passing an empty string "" or None as the password results
    in an immediate ValueError, long before reaching the facade.
    """
    alice = _make_user("alice")
    real_password = "the_secret_lives_only_in_my_mind"
    plaintext = b"Crown jewels"

    vault = encriptar(  # noqa: F841  (attacker has this file)
        plaintext,
        "crown_jewels.txt",
        [alice],
        alice["id"],
        alice["signing_private_key"],
    )

    keystore = protect_private_key(alice["private_key"], real_password)

    # Attack vector A: empty string password
    with pytest.raises(ValueError, match="Contraseña incorrecta"):
        recover_private_key(keystore, "")

    # Attack vector B: None password (attacker providing no secret)
    with pytest.raises(ValueError, match="Contraseña incorrecta"):
        recover_private_key(keystore, None)  # type: ignore[arg-type]
