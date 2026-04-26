import json
import struct
import pytest
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from secure_document_vault.core.facade import encriptar, desencriptar
from secure_document_vault.core.exceptions import IntegrityErrorException

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# SCENARIO 7: Multiple recipients (N > 2)
# Verifies the system scales correctly with large groups of users.
# ---------------------------------------------------------------------------


def test_multiple_recipients_all_can_decrypt():
    """All recipients in a large list can decrypt the file."""
    users = [create_user(f"user_{i}") for i in range(5)]
    plaintext = b"Document shared with 5 users"

    vault = encriptar(
        plaintext, "group.txt", users, users[0]["id"], users[0]["signing_private_key"]
    )

    for user in users:
        recovered = desencriptar(
            vault, user["id"], user["private_key"], users[0]["signing_public_key"]
        )
        assert recovered == plaintext


def test_multiple_recipients_non_member_cannot_decrypt():
    """A user outside the group of 5 cannot decrypt."""
    users = [create_user(f"user_{i}") for i in range(5)]
    outsider = create_user("outsider")
    plaintext = b"Group only content"

    vault = encriptar(
        plaintext, "private.txt", users, users[0]["id"], users[0]["signing_private_key"]
    )

    with pytest.raises(IntegrityErrorException, match="no autorizado"):
        desencriptar(
            vault,
            outsider["id"],
            outsider["private_key"],
            users[0]["signing_public_key"],
        )


# ---------------------------------------------------------------------------
# SCENARIO 8: Empty file
# Edge case: the system must handle a zero-byte plaintext.
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_empty_file():
    """An empty file can be encrypted and decrypted correctly."""
    alice = create_user("alice")
    plaintext = b""

    vault = encriptar(
        plaintext, "empty.txt", [alice], alice["id"], alice["signing_private_key"]
    )
    recovered = desencriptar(
        vault, "alice", alice["private_key"], alice["signing_public_key"]
    )

    assert recovered == plaintext


# ---------------------------------------------------------------------------
# SCENARIO 9: Binary files (non-text)
# Verifies the system works with arbitrary binary content
# such as images, PDFs, or executables.
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_binary_content():
    """Arbitrary binary content (simulates PDF/image) is encrypted and decrypted
    without loss."""
    alice = create_user("alice")
    # Simulates PDF header + arbitrary binary bytes
    plaintext = b"%PDF-1.4\x00\x01\x02\x03" + bytes(range(256)) * 4

    vault = encriptar(
        plaintext, "document.pdf", [alice], alice["id"], alice["signing_private_key"]
    )
    recovered = desencriptar(
        vault, "alice", alice["private_key"], alice["signing_public_key"]
    )

    assert recovered == plaintext


def test_encrypt_decrypt_binary_with_null_bytes():
    """Null bytes and extreme values (0x00, 0xFF) are preserved exactly."""
    alice = create_user("alice")
    plaintext = b"\x00" * 100 + b"\xff" * 100 + b"\x00\xff" * 50

    vault = encriptar(
        plaintext, "binary.bin", [alice], alice["id"], alice["signing_private_key"]
    )
    recovered = desencriptar(
        vault, "alice", alice["private_key"], alice["signing_public_key"]
    )

    assert recovered == plaintext


# ---------------------------------------------------------------------------
# SCENARIO 10: Large file
# Verifies integrity and correctness with larger data volumes.
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_large_file():
    """A 1 MB file is encrypted and decrypted with full integrity."""
    alice = create_user("alice")
    plaintext = b"A" * (1024 * 1024)  # 1 MB

    vault = encriptar(
        plaintext, "large_file.dat", [alice], alice["id"], alice["signing_private_key"]
    )
    recovered = desencriptar(
        vault, "alice", alice["private_key"], alice["signing_public_key"]
    )

    assert recovered == plaintext
    assert len(recovered) == 1024 * 1024


# ---------------------------------------------------------------------------
# SCENARIO 11: Single recipient
# Minimum case: a single recipient is the sole owner of the file.
# ---------------------------------------------------------------------------


def test_single_recipient_encrypt_decrypt():
    """The system works correctly with exactly one recipient."""
    alice = create_user("alice")
    plaintext = b"Only for Alice"

    vault = encriptar(
        plaintext, "alice_only.txt", [alice], alice["id"], alice["signing_private_key"]
    )
    recovered = desencriptar(
        vault, "alice", alice["private_key"], alice["signing_public_key"]
    )

    assert recovered == plaintext


def test_single_recipient_another_user_rejected():
    """With a single recipient, any other user is rejected."""
    alice = create_user("alice")
    bob = create_user("bob")
    plaintext = b"Only for Alice"

    vault = encriptar(
        plaintext, "alice_only.txt", [alice], alice["id"], alice["signing_private_key"]
    )

    with pytest.raises(IntegrityErrorException, match="no autorizado"):
        desencriptar(vault, bob["id"], bob["private_key"], alice["signing_public_key"])


# ---------------------------------------------------------------------------
# SCENARIO 12: Vault is immutable (multiple reads)
# The vault is not corrupted or changed when decrypted multiple times.
# ---------------------------------------------------------------------------


def test_vault_is_reusable_multiple_decryptions():
    """The same vault can be decrypted multiple times without degradation."""
    alice = create_user("alice")
    bob = create_user("bob")
    plaintext = b"Reusable message"

    vault = encriptar(
        plaintext,
        "reusable.txt",
        [alice, bob],
        alice["id"],
        alice["signing_private_key"],
    )

    for _ in range(3):
        assert (
            desencriptar(
                vault, "alice", alice["private_key"], alice["signing_public_key"]
            )
            == plaintext
        )
        assert (
            desencriptar(vault, "bob", bob["private_key"], alice["signing_public_key"])
            == plaintext
        )


# ---------------------------------------------------------------------------
# SCENARIO 13: Metadata integrity in the vault
# The metadata inside the vault must contain the correct information.
# ---------------------------------------------------------------------------


def test_vault_metadata_contains_filename():
    """The original filename is recorded in the vault metadata."""
    alice = create_user("alice")
    filename = "confidential_contract.pdf"

    vault = encriptar(
        b"Content", filename, [alice], alice["id"], alice["signing_private_key"]
    )

    # Manually parse the vault to read the AAD (JSON metadata)
    # Format: MAGIC(8) + NONCE(12) + META_LEN(4) + META(variable) + CIPHERTEXT
    meta_len = struct.unpack("<I", vault[20:24])[0]
    aad_bytes = vault[24 : 24 + meta_len]
    metadata = json.loads(aad_bytes.decode("utf-8"))

    assert metadata["file_name"] == filename


def test_vault_metadata_contains_all_recipient_ids():
    """The IDs of all recipients are recorded in the vault metadata."""
    alice = create_user("alice")
    bob = create_user("bob")
    carol = create_user("carol")
    recipients = [alice, bob, carol]

    vault = encriptar(
        b"Data", "multi.txt", recipients, alice["id"], alice["signing_private_key"]
    )

    meta_len = struct.unpack("<I", vault[20:24])[0]
    aad_bytes = vault[24 : 24 + meta_len]
    metadata = json.loads(aad_bytes.decode("utf-8"))

    ids_in_vault = {r["id"] for r in metadata["recipients"]}
    assert ids_in_vault == {"alice", "bob", "carol"}


def test_vault_metadata_algorithm_field():
    """The algorithm field in the metadata indicates ChaCha20-Poly1305."""
    alice = create_user("alice")
    vault = encriptar(
        b"Test", "test.txt", [alice], alice["id"], alice["signing_private_key"]
    )

    meta_len = struct.unpack("<I", vault[20:24])[0]
    aad_bytes = vault[24 : 24 + meta_len]
    metadata = json.loads(aad_bytes.decode("utf-8"))

    assert metadata["algorithm"] == "ChaCha20-Poly1305"


# ---------------------------------------------------------------------------
# SCENARIO 14: Each encryption produces a different vault (IND-CPA semantics)
# Two encryptions of the same plaintext produce different ciphertexts.
# ---------------------------------------------------------------------------


def test_two_encryptions_of_same_plaintext_differ():
    """Encrypting the same content twice produces different vaults (random nonce)."""
    alice = create_user("alice")
    plaintext = b"Same content"

    vault1 = encriptar(
        plaintext, "file.txt", [alice], alice["id"], alice["signing_private_key"]
    )
    vault2 = encriptar(
        plaintext, "file.txt", [alice], alice["id"], alice["signing_private_key"]
    )

    assert vault1 != vault2
    # Both can still be decrypted correctly
    assert (
        desencriptar(vault1, "alice", alice["private_key"], alice["signing_public_key"])
        == plaintext
    )
    assert (
        desencriptar(vault2, "alice", alice["private_key"], alice["signing_public_key"])
        == plaintext
    )


# ---------------------------------------------------------------------------
# SCENARIO 15: Vault with corrupted header
# The parser must reject files that are not valid vaults.
# ---------------------------------------------------------------------------


def test_invalid_header_raises_value_error():
    """A file with an incorrect header is rejected before attempting decryption."""
    alice = create_user("alice")
    fake_vault = b"FAKEHDR\x00" + b"\x00" * 100

    with pytest.raises(ValueError, match="Header incorrecto"):
        desencriptar(
            fake_vault, "alice", alice["private_key"], alice["signing_public_key"]
        )


def test_empty_bytes_raises_error():
    """Empty bytes are rejected as an invalid vault."""
    alice = create_user("alice")

    with pytest.raises(Exception):
        desencriptar(b"", "alice", alice["private_key"], alice["signing_public_key"])


def test_random_bytes_not_valid_vault():
    """Random bytes are not a valid vault and are rejected."""
    import os

    alice = create_user("alice")
    garbage = os.urandom(512)

    with pytest.raises(Exception):
        desencriptar(
            garbage, "alice", alice["private_key"], alice["signing_public_key"]
        )


# ---------------------------------------------------------------------------
# SCENARIO 16: Tampering with the wrapped key
# Modifying the encrypted key of a recipient prevents decryption.
# ---------------------------------------------------------------------------


def test_tampered_wrapped_key_fails():
    """Corrupting a recipient's wrapped key prevents decryption."""
    alice = create_user("alice")
    plaintext = b"Protected data"
    vault = encriptar(
        plaintext, "doc.txt", [alice], alice["id"], alice["signing_private_key"]
    )

    # The AAD is pure ASCII JSON (hex strings). We locate the "encrypted_key"
    # substring and corrupt one byte of the hex value that follows.
    meta_len = struct.unpack("<I", vault[20:24])[0]
    aad_start = 24
    aad_bytes = vault[aad_start : aad_start + meta_len]

    # Find the position of "encrypted_key" inside the AAD to corrupt its value
    marker = b'"encrypted_key"'
    marker_pos = aad_bytes.find(marker)
    assert marker_pos != -1, "'encrypted_key' not found in AAD"

    # Skip the marker + '": "' to reach the hex value (safe ASCII bytes to corrupt)
    target = aad_start + marker_pos + len(marker) + 5  # +5 for '": "'

    corrupted = bytearray(vault)
    # Replace one hex digit with another (remains valid UTF-8)
    original = corrupted[target]
    corrupted[target] = ord("0") if original != ord("0") else ord("1")

    with pytest.raises(IntegrityErrorException):
        desencriptar(
            bytes(corrupted), "alice", alice["private_key"], alice["signing_public_key"]
        )


# ---------------------------------------------------------------------------
# SCENARIO 17: Each recipient has a unique wrapped key
# Each recipient receives their own wrapped key (no shared cryptographic material).
# ---------------------------------------------------------------------------


def test_each_recipient_has_unique_wrapped_key():
    """Each recipient has their own unique wrapped key (different ephemeral key)."""
    alice = create_user("alice")
    bob = create_user("bob")

    vault = encriptar(
        b"Shared", "shared.txt", [alice, bob], alice["id"], alice["signing_private_key"]
    )

    meta_len = struct.unpack("<I", vault[20:24])[0]
    aad_bytes = vault[24 : 24 + meta_len]
    metadata = json.loads(aad_bytes.decode("utf-8"))

    recipients = metadata["recipients"]
    assert len(recipients) == 2

    key_alice = recipients[0]["encrypted_key"]["encrypted_key"]
    key_bob = recipients[1]["encrypted_key"]["encrypted_key"]

    # Encrypted keys must be different
    assert key_alice != key_bob

    ephemeral_alice = recipients[0]["encrypted_key"]["ephemeral_pub"]
    ephemeral_bob = recipients[1]["encrypted_key"]["ephemeral_pub"]

    # Ephemeral public keys must also be different
    assert ephemeral_alice != ephemeral_bob


# ---------------------------------------------------------------------------
# SCENARIO 18: Filename with special characters
# The system must handle names with spaces, accents, and Unicode symbols.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre",
    [
        "document with spaces.txt",
        "final_report_2024.pdf",
        "archivo_español_ñoño.docx",
        "文件.txt",
        "fichier très important.pdf",
    ],
)
def test_encrypt_decrypt_special_filename(nombre):
    """Filenames with special characters are preserved in the vault metadata."""
    alice = create_user("alice")
    plaintext = b"File content"

    vault = encriptar(
        plaintext, nombre, [alice], alice["id"], alice["signing_private_key"]
    )
    recovered = desencriptar(
        vault, "alice", alice["private_key"], alice["signing_public_key"]
    )

    assert recovered == plaintext

    meta_len = struct.unpack("<I", vault[20:24])[0]
    aad_bytes = vault[24 : 24 + meta_len]
    metadata = json.loads(aad_bytes.decode("utf-8"))

    assert metadata["file_name"] == nombre


# ---------------------------------------------------------------------------
# SCENARIO 19: Full end-to-end flow with multiple file types
# Simulates a real use case: different formats shared between users.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre,contenido",
    [
        ("contract.txt", b"Non-disclosure agreement signed digitally."),
        ("image.png", b"\x89PNG\r\n\x1a\n" + bytes(range(200))),
        ("data.csv", b"id,name,salary\n1,Alice,50000\n2,Bob,60000\n"),
        ("config.json", b'{"key": "value", "active": true}'),
    ],
)
def test_end_to_end_file_types(nombre, contenido):
    """Full flow for different file types with multiple recipients."""
    alice = create_user("alice")
    bob = create_user("bob")

    vault = encriptar(
        contenido, nombre, [alice, bob], alice["id"], alice["signing_private_key"]
    )

    assert (
        desencriptar(vault, "alice", alice["private_key"], alice["signing_public_key"])
        == contenido
    )
    assert (
        desencriptar(vault, "bob", bob["private_key"], alice["signing_public_key"])
        == contenido
    )


# ---------------------------------------------------------------------------
# SCENARIO 20: Removing a recipient entry breaks access
# Editing the AAD JSON to remove a user from the recipients list must prevent
# that user from decrypting. The AEAD tag also fails because the AAD changed,
# so even remaining recipients cannot decrypt the tampered vault.
# ---------------------------------------------------------------------------


def test_removing_recipient_entry_breaks_access():
    """Removing Bob from the recipients list in the vault prevents him from
    decrypting."""
    alice = create_user("alice")
    bob = create_user("bob")
    plaintext = b"Shared document"

    vault = encriptar(
        plaintext, "shared.txt", [alice, bob], alice["id"], alice["signing_private_key"]
    )

    # Parse the vault and extract its components
    meta_len = struct.unpack("<I", vault[20:24])[0]
    aad_bytes = vault[24 : 24 + meta_len]
    metadata = json.loads(aad_bytes.decode("utf-8"))

    # Remove Bob's entry from the recipients list
    metadata["recipients"] = [r for r in metadata["recipients"] if r["id"] != "bob"]

    # Re-serialize the AAD without Bob
    new_aad = json.dumps(metadata).encode("utf-8")
    new_meta_len = struct.pack("<I", len(new_aad))

    # Rebuild the vault with the modified AAD
    nonce = vault[8:20]
    ciphertext = vault[24 + meta_len :]
    tampered_vault = vault[:8] + nonce + new_meta_len + new_aad + ciphertext

    # Bob is no longer in the list — must be rejected.
    # Because we tampered with the AAD, the signature check fails first.
    with pytest.raises(IntegrityErrorException, match="Firma digital"):
        desencriptar(
            tampered_vault, "bob", bob["private_key"], alice["signing_public_key"]
        )

    # Alice cannot decrypt either: the AAD changed so the AEAD tag no longer matches
    with pytest.raises(IntegrityErrorException):
        desencriptar(
            tampered_vault, "alice", alice["private_key"], alice["signing_public_key"]
        )
