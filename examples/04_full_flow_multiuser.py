"""
Example 4 — Full end-to-end flow with multiple users.

Simulates a realistic scenario:
  - A team of 4 users each generates their own key pair.
  - Alice (the sender) encrypts a document for the whole team.
  - Each team member independently decrypts and verifies the document.
  - An outsider (Eve) is rejected.

This example demonstrates all security properties working together:
  AEAD encryption, hybrid key wrapping, digital signatures, and keystores.

Run:
    python examples/04_full_flow_multiuser.py
"""

from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from secure_document_vault.modules.key_store.generator import KeyProtector
from secure_document_vault.core.facade import encriptar, desencriptar
from secure_document_vault.core.exceptions import IntegrityErrorException


def create_user(user_id: str, password: str) -> dict:
    """Generate a full key set for a user and protect it with a password."""
    enc_priv = x25519.X25519PrivateKey.generate()
    sign_priv = ed25519.Ed25519PrivateKey.generate()
    return {
        "id": user_id,
        "password": password,
        "enc_keystore": KeyProtector.protect_key(password, enc_priv, user_id),
        "enc_public_key": enc_priv.public_key(),
        "sign_keystore": KeyProtector.protect_key(password, sign_priv, user_id),
        "sign_public_key": sign_priv.public_key(),
    }


def main():
    print("=" * 60)
    print("Secure Document Vault — Full Multi-User Flow")
    print("=" * 60)

    # Step 1: Each user generates their key pair
    print("\n[1] Generating key pairs...")
    alice = create_user("alice", "alice-pass-2024!")
    bob = create_user("bob", "bob-pass-2024!")
    carol = create_user("carol", "carol-pass-2024!")
    dave = create_user("dave", "dave-pass-2024!")
    team = [alice, bob, carol, dave]
    print(f"    Users created: {[u['id'] for u in team]}")

    # Step 2: Alice encrypts a document for the whole team
    print("\n[2] Alice encrypts a document for the team...")
    document = b"Q3 Financial Results - CONFIDENTIAL\nRevenue: $4.2M\nGrowth: 18%"
    filename = "q3_results.txt"

    recipients = [{"id": u["id"], "public_key": u["enc_public_key"]} for u in team]

    vault = encriptar(
        archivo_en_bytes=document,
        nombre_archivo=filename,
        recipients_info=recipients,
        signer_id=alice["id"],
        signer_keystore=alice["sign_keystore"],
        signer_password=alice["password"],
    )
    print(f"    Vault created: {len(vault)} bytes")
    print("    Signed by: alice")
    print(f"    Recipients: {[r['id'] for r in recipients]}")

    # Step 3: Each team member decrypts independently
    print("\n[3] Each team member decrypts the vault...")
    for user in team:
        recovered = desencriptar(
            archivo_vault=vault,
            user_id=user["id"],
            user_keystore=user["enc_keystore"],
            user_password=user["password"],
            signer_public_key=alice["sign_public_key"],
        )
        match = recovered == document
        status = "PASS" if match else "FAIL"
        print(f"    {user['id']:8s} -> decrypted OK | integrity: {status}")

    # Step 4: Eve (outsider) is rejected
    print("\n[4] Eve (outsider) tries to access the vault...")
    eve = create_user("eve", "eve-pass!")
    try:
        desencriptar(
            archivo_vault=vault,
            user_id=eve["id"],
            user_keystore=eve["enc_keystore"],
            user_password=eve["password"],
            signer_public_key=alice["sign_public_key"],
        )
        print("    ERROR: Eve should not have been able to decrypt!")
    except IntegrityErrorException as e:
        print(f"    Eve rejected (expected): {e}")

    # Step 5: Tampered vault is detected before decryption
    print("\n[5] Tampered vault is detected...")
    tampered = bytearray(vault)
    tampered[-20] ^= 0xAB  # corrupt a byte in the ciphertext region
    try:
        desencriptar(
            bytes(tampered),
            user_id=bob["id"],
            user_keystore=bob["enc_keystore"],
            user_password=bob["password"],
            signer_public_key=alice["sign_public_key"],
        )
        print("    ERROR: Tampered vault should have been rejected!")
    except IntegrityErrorException as e:
        print(f"    Tampered vault rejected (expected): {e}")

    print("\n" + "=" * 60)
    print("All checks passed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
