"""
Example 2 — Encrypt a document for one or more recipients.

Reads a plaintext file, encrypts it into the .vault format using hybrid
encryption (X25519 + ChaCha20-Poly1305) and signs it with Ed25519.
The output .vault file can only be decrypted by listed recipients.

Run:
    python examples/02_encrypt_document.py
"""

from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from secure_document_vault.modules.key_store.generator import KeyProtector
from secure_document_vault.core.facade import encriptar

OUTPUT_DIR = Path("examples/output")
OUTPUT_DIR.mkdir(exist_ok=True)


def setup_demo_users():
    """Create two in-memory users (alice = signer, bob = recipient)."""
    alice_enc_priv = x25519.X25519PrivateKey.generate()
    alice_sign_priv = ed25519.Ed25519PrivateKey.generate()

    bob_enc_priv = x25519.X25519PrivateKey.generate()

    users = {
        "alice": {
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
        },
        "bob": {
            "id": "bob",
            "password": "bob-password",
            "enc_keystore": KeyProtector.protect_key(
                "bob-password", bob_enc_priv, "bob"
            ),
            "enc_public_key": bob_enc_priv.public_key(),
        },
    }
    return users


def main():
    users = setup_demo_users()
    alice = users["alice"]
    bob = users["bob"]

    # The document to encrypt (any bytes — text, PDF, image, etc.)
    document_name = "confidential_report.txt"
    document_bytes = b"This is a confidential report. Only Alice and Bob can read this."

    # Recipients: a list of dicts with 'id' and 'public_key' (X25519)
    recipients = [
        {"id": alice["id"], "public_key": alice["enc_public_key"]},
        {"id": bob["id"], "public_key": bob["enc_public_key"]},
    ]

    recipient_ids = [r['id'] for r in recipients]
    print(f"Encrypting '{document_name}' for recipients: {recipient_ids}")
    print(f"Signer: {alice['id']}")

    vault_bytes = encriptar(
        archivo_en_bytes=document_bytes,
        nombre_archivo=document_name,
        recipients_info=recipients,
        signer_id=alice["id"],
        signer_keystore=alice["sign_keystore"],
        signer_password=alice["password"],
    )

    # Save the vault file
    vault_path = OUTPUT_DIR / f"{document_name}.vault"
    vault_path.write_bytes(vault_bytes)
    print(f"\nVault saved to: {vault_path}")
    print(f"Original size: {len(document_bytes)} bytes")
    print(f"Vault size:    {len(vault_bytes)} bytes")
    print("\nEncryption successful. The vault can only be decrypted by Alice and Bob.")


if __name__ == "__main__":
    main()
