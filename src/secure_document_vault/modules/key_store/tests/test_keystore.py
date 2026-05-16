import pytest
import json
import base64
from cryptography.hazmat.primitives import serialization
from secure_document_vault.modules.key_store.generator import KeyProtector
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519


def create_user(user_id):
    """Creates a user with X25519 and Ed25519 key pairs."""
    x_priv = x25519.X25519PrivateKey.generate()
    e_priv = ed25519.Ed25519PrivateKey.generate()
    return {
        "id": user_id,
        "private_key": x_priv,
        "public_key": x_priv.public_key(),
        "signing_private_key": e_priv,
        "signing_public_key": e_priv.public_key(),
    }


def test_correct_password():
    """Verifies that access is granted when password is correct"""
    bob = create_user("bob-123")
    # Derive KEK
    protected_key_dict = KeyProtector.protect_key(
        "Secret_password-123", bob["private_key"], bob["id"]
    )

    # Get the original key with the password
    recovered_key = KeyProtector.verify_password(
        "Secret_password-123", protected_key_dict
    )

    original_key_bytes = (
        bob["private_key"]
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
    )
    recovered_key_bytes = recovered_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )

    assert original_key_bytes == recovered_key_bytes


def test_wrong_password():
    """Verifies that access is not granted when password is incorrect"""
    bob = create_user("bob-123")
    # Derive KEK
    protected_key_dict = KeyProtector.protect_key(
        "Secret_password-123", bob["private_key"], bob["id"]
    )

    with pytest.raises(ValueError, match="CONTRASEÑA INCORRECTA O KEYSTORE CORRUPTO"):
        KeyProtector.verify_password("Incorrect_password-123", protected_key_dict)


def test_modified_keystore():
    """Verifies if keystore is modified"""
    alice = create_user("alice-567")
    protected_key_dict = KeyProtector.protect_key(
        "password-12345", alice["private_key"], alice["id"]
    )

    protected_key = protected_key_dict["encrypted_key"]

    # Simulate an attack
    # Decode key
    decoded_key = bytearray(base64.b64decode(protected_key))

    # Modify a bit
    decoded_key[0] ^= 1

    # Store again in the dict and try to get the key again
    encoded_key = base64.b64encode(decoded_key).decode("utf-8")
    protected_key_dict["encrypted_key"] = encoded_key

    # Try to get the key with the correct password
    with pytest.raises(ValueError, match="CONTRASEÑA INCORRECTA O KEYSTORE CORRUPTO"):
        KeyProtector.verify_password("password-12345", protected_key_dict)


def test_backup():
    """Verifies that restoring keys works"""
    password = "MySecureBackupPassword!"
    original_private_key = ed25519.Ed25519PrivateKey.generate()

    keystore_dict = KeyProtector.protect_key(
        password, original_private_key, "user-backup"
    )

    backup_json_string = json.dumps(keystore_dict)

    # ... Some time passes, the user uses another device ...

    restored_dict = json.loads(backup_json_string)

    recovered_key = KeyProtector.verify_password(password, restored_dict)

    original_pub_bytes = original_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    recovered_pub_bytes = recovered_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )

    assert original_pub_bytes == recovered_pub_bytes


def test_stolen_keystore_alone():
    """Verifies that when keystore is stolen, cannot decrypt anything"""
    password = "UserStrongPassword"
    original_private_key = ed25519.Ed25519PrivateKey.generate()

    stolen_keystore = KeyProtector.protect_key(
        password, original_private_key, "user-victim"
    )

    raw_stolen_bytes = base64.b64decode(stolen_keystore["encrypted_key"])

    with pytest.raises(ValueError):
        serialization.load_pem_private_key(raw_stolen_bytes, password=None)

    attacker_guesses = ["123456", "password", "admin", "user-victim"]

    for guess in attacker_guesses:
        with pytest.raises(
            ValueError, match="""CONTRASEÑA INCORRECTA O KEYSTORE CORRUPTO"""
        ):
            KeyProtector.verify_password(guess, stolen_keystore)
