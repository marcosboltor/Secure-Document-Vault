"""
Example 5 — Key lifecycle: rotation and revocation.

Demonstrates the key management operations supported by KeyProtector:
  - Creating a keystore with an expiration date
  - Checking expiration status
  - Rotating a key (retiring the old one, protecting a new one)
  - Revoking a key (marking it as compromised)
  - Validating keystore integrity without a password

Run:
    python examples/05_key_lifecycle.py
"""

from cryptography.hazmat.primitives.asymmetric import x25519
from secure_document_vault.modules.key_store.generator import KeyProtector


def section(title: str):
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print(f"{'=' * 55}")


def main():
    password = "initial-password-2024"

    # ----------------------------------------------------------------
    # 1. Create a keystore with an expiration date
    # ----------------------------------------------------------------
    section("1. Create keystore with expiration")

    private_key = x25519.X25519PrivateKey.generate()
    keystore = KeyProtector.protect_key(
        password=password,
        private_key_obj=private_key,
        user_id="alice",
        expires_in_days=365,
    )

    print(f"Key ID:      {keystore['metadata']['key_id']}")
    print(f"Status:      {keystore['metadata']['status']}")
    print(f"Created:     {keystore['metadata']['creation_date']}")
    print(f"Expires at:  {keystore['metadata'].get('expires_at', 'N/A')}")

    # ----------------------------------------------------------------
    # 2. Check expiration status
    # ----------------------------------------------------------------
    section("2. Check expiration")

    is_expired, message = KeyProtector.check_expiration(keystore)
    print(f"Expired: {is_expired}")
    print(f"Message: {message}")

    # ----------------------------------------------------------------
    # 3. Validate keystore integrity (no password needed)
    # ----------------------------------------------------------------
    section("3. Validate keystore integrity")

    is_valid, reason = KeyProtector.validate_keystore(keystore)
    print(f"Valid:  {is_valid}")
    print(f"Reason: {reason}")

    # Simulate corruption
    corrupted = dict(keystore)
    corrupted["checksum"] = "0" * 64
    is_valid_corrupted, reason_corrupted = KeyProtector.validate_keystore(corrupted)
    print("\nCorrupted keystore:")
    print(f"Valid:  {is_valid_corrupted}")
    print(f"Reason: {reason_corrupted}")

    # ----------------------------------------------------------------
    # 4. Rotate the key
    # ----------------------------------------------------------------
    section("4. Key rotation")

    new_private_key = x25519.X25519PrivateKey.generate()
    new_keystore, retired_keystore = KeyProtector.rotate_key(
        old_keystore=keystore,
        password=password,
        new_private_key_obj=new_private_key,
        new_password="new-password-2025",
    )

    print(f"Old key status: {retired_keystore['metadata']['status']}")
    print(f"Old rotated_at: {retired_keystore['metadata'].get('rotated_at', 'N/A')}")
    print(f"\nNew key ID:     {new_keystore['metadata']['key_id']}")
    print(f"New key status: {new_keystore['metadata']['status']}")
    print(f"Rotated from:   {new_keystore['metadata'].get('rotated_from', 'N/A')}")

    # ----------------------------------------------------------------
    # 5. Revoke a key
    # ----------------------------------------------------------------
    section("5. Key revocation")

    revoked_keystore = KeyProtector.revoke_key(new_keystore)
    print(f"Status after revocation: {revoked_keystore['metadata']['status']}")
    print(f"Revoked at: {revoked_keystore['metadata'].get('revoked_at', 'N/A')}")

    # Attempting to use a revoked key raises an error
    print("\nAttempting to unlock revoked key...")
    try:
        KeyProtector.verify_password("new-password-2025", revoked_keystore)
        print("ERROR: Revoked key should not be unlockable!")
    except ValueError as e:
        print(f"Correctly rejected: {e}")

    # ----------------------------------------------------------------
    # 6. Lifecycle status helper
    # ----------------------------------------------------------------
    section("6. Lifecycle status checks")

    print(f"Original keystore status: {KeyProtector.get_key_status(keystore)}")
    print(f"Retired keystore status:  {KeyProtector.get_key_status(retired_keystore)}")
    print(f"Revoked keystore status:  {KeyProtector.get_key_status(revoked_keystore)}")


if __name__ == "__main__":
    main()
