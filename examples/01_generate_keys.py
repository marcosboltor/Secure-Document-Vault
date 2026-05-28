"""
Example 1 — Generate and save a user's key pair.

Generates an X25519 encryption key and an Ed25519 signing key for a user,
protects both with a password using PBKDF2 + ChaCha20-Poly1305, and saves
them to the keys/ directory as a keystore bundle.

Run:
    python examples/01_generate_keys.py
"""

from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives import serialization
from secure_document_vault.modules.key_store.generator import KeyProtector

KEYS_DIR = Path("keys")
KEYS_DIR.mkdir(exist_ok=True)


def generate_user_keys(user_id: str, password: str) -> dict:
    """Generate X25519 + Ed25519 key pairs for a user and return a keystore bundle."""
    enc_private = x25519.X25519PrivateKey.generate()
    sign_private = ed25519.Ed25519PrivateKey.generate()

    enc_keystore = KeyProtector.protect_key(password, enc_private, user_id)
    sign_keystore = KeyProtector.protect_key(password, sign_private, user_id)

    bundle = KeyProtector.export_keystore_bundle(
        enc_keystore=enc_keystore,
        sign_keystore=sign_keystore,
        user_name=user_id,
        user_id=user_id,
    )

    # Also return the public keys (safe to share)
    enc_public_pem = enc_private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    sign_public_pem = sign_private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    return bundle, enc_public_pem, sign_public_pem


def main():
    user_id = "alice"
    password = "my-secure-password-123"

    print(f"Generating keys for user: {user_id}")
    bundle, enc_pub, sign_pub = generate_user_keys(user_id, password)

    # Save the encrypted bundle to disk
    bundle_path = KEYS_DIR / f"{user_id}_bundle.json"
    KeyProtector.backup_keystore(bundle, str(bundle_path))
    print(f"Keystore bundle saved to: {bundle_path}")

    # Save public keys (these can be shared with others)
    enc_pub_path = KEYS_DIR / f"{user_id}_enc_public.pem"
    sign_pub_path = KEYS_DIR / f"{user_id}_sign_public.pem"
    enc_pub_path.write_text(enc_pub)
    sign_pub_path.write_text(sign_pub)
    print(f"Encryption public key saved to: {enc_pub_path}")
    print(f"Signing public key saved to:    {sign_pub_path}")

    # Verify the bundle is valid before finishing
    is_valid, reason, _ = KeyProtector.import_keystore_bundle(bundle)
    print(f"\nBundle validation: {'OK' if is_valid else 'FAILED'} — {reason}")

    print("\nKey IDs:")
    enc_id = bundle['keystores']['encryption']['metadata']['key_id']
    sign_id = bundle['keystores']['signing']['metadata']['key_id']
    print(f"  Encryption key: {enc_id}")
    print(f"  Signing key:    {sign_id}")


if __name__ == "__main__":
    main()
