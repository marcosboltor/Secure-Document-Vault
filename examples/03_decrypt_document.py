"""
Example 3 — Decrypt a .vault file.

Shows how a recipient decrypts a vault file. The system first verifies the
Ed25519 signature — if tampering is detected, decryption is refused entirely.
Only listed recipients can successfully decrypt.

Run:
    python examples/03_decrypt_document.py
"""

from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from secure_document_vault.modules.key_store.generator import KeyProtector
from secure_document_vault.core.facade import encriptar, desencriptar
from secure_document_vault.core.exceptions import IntegrityErrorException

OUTPUT_DIR = Path("examples/output")
OUTPUT_DIR.mkdir(exist_ok=True)


def setup_demo_users():
    """Same two users as in example 2."""
    alice_enc_priv = x25519.X25519PrivateKey.generate()
    alice_sign_priv = ed25519.Ed25519PrivateKey.generate()
    bob_enc_priv = x25519.X25519PrivateKey.generate()

    alice = {
        "id": "alice",
        "password": "alice-password",
        "enc_keystore": KeyProtector.protect_key(
            "alice-password", alice_enc_priv, "alice"
        ),
        "enc_public_key": alice_enc_priv.public_key(),
        "sign_keystore": KeyProtector.protect_key(
            "alice-password", alice_sign_priv, "alice"
        ),
        "sign_public_key": alice_sign_priv.public_key(),
    }
    bob = {
        "id": "bob",
        "password": "bob-password",
        "enc_keystore": KeyProtector.protect_key(
            "bob-password", bob_enc_priv, "bob"
        ),
        "enc_public_key": bob_enc_priv.public_key(),
    }
    return alice, bob


def main():
    alice, bob = setup_demo_users()

    # 1. Encrypt a document (re-creating the vault from example 2 in memory)
    document_name = "confidential_report.txt"
    document_bytes = b"This is a confidential report. Only Alice and Bob can read this."

    recipients = [
        {"id": alice["id"], "public_key": alice["enc_public_key"]},
        {"id": bob["id"], "public_key": bob["enc_public_key"]},
    ]

    vault_bytes = encriptar(
        archivo_en_bytes=document_bytes,
        nombre_archivo=document_name,
        recipients_info=recipients,
        signer_id=alice["id"],
        signer_keystore=alice["sign_keystore"],
        signer_password=alice["password"],
    )

    print(f"Vault created ({len(vault_bytes)} bytes)\n")

    # 2. Bob decrypts the vault
    print("--- Bob decrypts ---")
    recovered = desencriptar(
        archivo_vault=vault_bytes,
        user_id=bob["id"],
        user_keystore=bob["enc_keystore"],
        user_password=bob["password"],
        signer_public_key=alice["sign_public_key"],
    )
    print(f"Decrypted content: {recovered.decode()}")
    print("Integrity check:   OK (signature verified)\n")

    # 3. Alice also decrypts
    print("--- Alice decrypts ---")
    recovered_alice = desencriptar(
        archivo_vault=vault_bytes,
        user_id=alice["id"],
        user_keystore=alice["enc_keystore"],
        user_password=alice["password"],
        signer_public_key=alice["sign_public_key"],
    )
    print(f"Decrypted content: {recovered_alice.decode()}")
    print("Integrity check:   OK (signature verified)\n")

    # 4. Show what happens with an unauthorized user
    print("--- Unauthorized user tries to decrypt ---")
    eve_enc_priv = x25519.X25519PrivateKey.generate()
    eve = {
        "id": "eve",
        "password": "eve-password",
        "enc_keystore": KeyProtector.protect_key("eve-password", eve_enc_priv, "eve"),
    }
    try:
        desencriptar(
            archivo_vault=vault_bytes,
            user_id=eve["id"],
            user_keystore=eve["enc_keystore"],
            user_password=eve["password"],
            signer_public_key=alice["sign_public_key"],
        )
    except IntegrityErrorException as e:
        print(f"Access denied for 'eve': {e}\n")

    # 5. Show what happens when the vault is tampered
    print("--- Tampered vault detection ---")
    tampered = bytearray(vault_bytes)
    tampered[50] ^= 0xFF  # corrupt one byte
    try:
        desencriptar(
            bytes(tampered),
            user_id=bob["id"],
            user_keystore=bob["enc_keystore"],
            user_password=bob["password"],
            signer_public_key=alice["sign_public_key"],
        )
    except IntegrityErrorException as e:
        print(f"Tampered vault rejected: {e}")


if __name__ == "__main__":
    main()
