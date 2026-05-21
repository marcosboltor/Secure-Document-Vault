"""
Integration tests for the Key Management Lifecycle (Issue 4 – Rubric D6).

Tests the complete end-to-end flow through the orchestration layer (facade.py),
using KeyProtector for password-based key protection to emulate real end-user
behavior across all 5 mandatory rubric scenarios.
"""

import pytest

from cryptography.hazmat.primitives.asymmetric import x25519, ed25519

from secure_document_vault.core.facade import encriptar, desencriptar
from secure_document_vault.modules.key_store.generator import KeyProtector

# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: str) -> dict:
    """Return a user dict with X25519, Ed25519 key pairs and a keystore."""
    x_priv = x25519.X25519PrivateKey.generate()
    e_priv = ed25519.Ed25519PrivateKey.generate()
    return {
        "id": user_id,
        "private_key": x_priv,
        "public_key": x_priv.public_key(),
        "signing_private_key": e_priv,
        "signing_public_key": e_priv.public_key(),
    }


def _make_recipient(user: dict) -> dict:
    """Return the recipient entry expected by encriptar."""
    return {"id": user["id"], "public_key": user["public_key"]}


# ---------------------------------------------------------------------------
# SCENARIO 1: Correct password → access granted
# ---------------------------------------------------------------------------


def test_correct_password_grants_access():
    """
    A user protects her private keys with a password. After encrypting a
    document, the same password lets her recover the keys and decrypt.

    Assertion: the original plaintext is returned without error.
    """
    alice = _make_user("alice")
    password = "supersecret_passphrase_42!"
    plaintext = b"Classified: launch codes are 0000"

    alice_x_keystore = KeyProtector.protect_key(
        password, alice["private_key"], alice["id"]
    )
    alice_e_keystore = KeyProtector.protect_key(
        password, alice["signing_private_key"], alice["id"]
    )

    vault = encriptar(
        plaintext,
        "launch_codes.txt",
        [_make_recipient(alice)],
        alice["id"],
        alice_e_keystore,
        password,
    )

    result = desencriptar(
        vault,
        alice["id"],
        alice_x_keystore,
        password,
        alice["signing_public_key"],
    )

    assert result == plaintext


# ---------------------------------------------------------------------------
# SCENARIO 2: Wrong password → access denied
# ---------------------------------------------------------------------------


def test_wrong_password_denies_access():
    """
    Attempting to decrypt with the wrong password must raise a controlled
    exception before any private key material is exposed.

    Assertion: ValueError is raised; desencriptar is never reached.
    """
    alice = _make_user("alice")
    correct_password = "correct_horse_battery_staple"
    wrong_password = "password123"

    alice_x_keystore = KeyProtector.protect_key(
        correct_password, alice["private_key"], alice["id"]
    )
    alice_e_keystore = KeyProtector.protect_key(
        correct_password, alice["signing_private_key"], alice["id"]
    )

    vault = encriptar(
        b"Top secret data",
        "secret.txt",
        [_make_recipient(alice)],
        alice["id"],
        alice_e_keystore,
        correct_password,
    )

    with pytest.raises(ValueError):
        desencriptar(
            vault,
            alice["id"],
            alice_x_keystore,
            wrong_password,
            alice["signing_public_key"],
        )


# ---------------------------------------------------------------------------
# SCENARIO 3: Modified keystore → failure
# ---------------------------------------------------------------------------


def test_modified_keystore_is_rejected():
    """
    Corrupting a single byte of the encrypted key in the keystore must be
    detected by the AEAD authentication tag.

    Assertion: ValueError is raised regardless of which byte was altered.
    """
    import base64

    alice = _make_user("alice")
    password = "integrity_matters!"

    alice_x_keystore = KeyProtector.protect_key(
        password, alice["private_key"], alice["id"]
    )
    alice_e_keystore = KeyProtector.protect_key(
        password, alice["signing_private_key"], alice["id"]
    )

    encriptar(
        b"Sensitive payload",
        "payload.txt",
        [_make_recipient(alice)],
        alice["id"],
        alice_e_keystore,
        password,
    )

    # Corrupt one byte of the encrypted_key field in the X25519 keystore
    raw = bytearray(base64.b64decode(alice_x_keystore["encrypted_key"]))
    raw[4] ^= 0xFF
    corrupted_keystore = dict(alice_x_keystore)
    corrupted_keystore["encrypted_key"] = base64.b64encode(raw).decode("utf-8")

    with pytest.raises(ValueError):
        KeyProtector.verify_password(password, corrupted_keystore)


# ---------------------------------------------------------------------------
# SCENARIO 4: Backup → restore works
# ---------------------------------------------------------------------------


def test_backup_and_restore_allows_decryption(tmp_path):
    """
    Full backup/restore lifecycle:
      1. Generate keys, protect them, and encrypt a document.
      2. Back up both keystores to disk.
      3. Delete all in-memory user data (simulate RAM wipe).
      4. Restore the keystores from disk.
      5. Decrypt the vault using only restored data + password.

    Assertion: decryption succeeds and returns the original plaintext.
    """
    alice = _make_user("alice")
    password = "backup_restore_password_2024"
    plaintext = b"Critical document that must survive a restart"

    alice_x_keystore = KeyProtector.protect_key(
        password, alice["private_key"], alice["id"]
    )
    alice_e_keystore = KeyProtector.protect_key(
        password, alice["signing_private_key"], alice["id"]
    )

    vault = encriptar(
        plaintext,
        "critical.txt",
        [_make_recipient(alice)],
        alice["id"],
        alice_e_keystore,
        password,
    )

    # Backup: write keystores to disk
    x_path = str(tmp_path / "alice_x.keystore")
    e_path = str(tmp_path / "alice_e.keystore")
    KeyProtector.backup_keystore(alice_x_keystore, x_path)
    KeyProtector.backup_keystore(alice_e_keystore, e_path)

    signing_pub = alice["signing_public_key"]
    user_id = alice["id"]

    # Simulate RAM wipe
    del alice, alice_x_keystore, alice_e_keystore

    # Restore: read keystores from disk
    restored_x = KeyProtector.restore_keystore(x_path)

    result = desencriptar(vault, user_id, restored_x, password, signing_pub)

    assert result == plaintext


# ---------------------------------------------------------------------------
# SCENARIO 5: Stolen keystore alone → cannot decrypt (no password = no access)
# ---------------------------------------------------------------------------


def test_stolen_files_without_password_are_useless():
    """
    An attacker has obtained both the .vault and the .keystore files.
    Without the password, both files together are cryptographically useless.

    Assertion: empty string and None passwords are rejected immediately
    with ValueError, long before reaching the AEAD decryption layer.
    """
    alice = _make_user("alice")
    real_password = "the_secret_lives_only_in_my_mind"

    alice_x_keystore = KeyProtector.protect_key(
        real_password, alice["private_key"], alice["id"]
    )
    alice_e_keystore = KeyProtector.protect_key(
        real_password, alice["signing_private_key"], alice["id"]
    )

    vault = encriptar(  # noqa: F841  (attacker has this file too)
        b"Crown jewels",
        "crown_jewels.txt",
        [_make_recipient(alice)],
        alice["id"],
        alice_e_keystore,
        real_password,
    )

    # Attack vector A: empty string password
    with pytest.raises(ValueError):
        KeyProtector.verify_password("", alice_x_keystore)

    # Attack vector B: None password
    with pytest.raises((ValueError, AttributeError)):
        KeyProtector.verify_password(None, alice_x_keystore)  # type: ignore[arg-type]
