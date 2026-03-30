import secrets
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


class ECCKeyWrapper:
    """
    Key Wrapping module using ECC (X25519 + HKDF + AEAD).
    Responsible for securely encrypting (wrapping) the symmetric file_key
    for each recipient.
    """

    @staticmethod
    def _derive_key(shared_secret: bytes) -> bytes:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=None,
            info=b"file-key-wrap",
        )
        return hkdf.derive(shared_secret)

    @staticmethod
    def wrap_key(file_key: bytes, recipient_public_key) -> dict:
        ephemeral_private_key = x25519.X25519PrivateKey.generate()
        ephemeral_public_key = ephemeral_private_key.public_key()
        shared_secret = ephemeral_private_key.exchange(recipient_public_key)
        wrapping_key = ECCKeyWrapper._derive_key(shared_secret)

        nonce = secrets.token_bytes(12)  # 96-bit nonce
        aead = ChaCha20Poly1305(wrapping_key)
        encrypted_key = aead.encrypt(nonce, file_key, None)

        ephemeral_pub_bytes = ephemeral_public_key.public_bytes_raw()

        return {
            "ephemeral_pub": ephemeral_pub_bytes.hex(),
            "nonce": nonce.hex(),
            "encrypted_key": encrypted_key.hex(),
        }

    @staticmethod
    def unwrap_key(wrapped_data: dict, recipient_private_key) -> bytes:
        ephemeral_pub_bytes = bytes.fromhex(wrapped_data["ephemeral_pub"])
        ephemeral_public_key = x25519.X25519PublicKey.from_public_bytes(
            ephemeral_pub_bytes
        )

        shared_secret = recipient_private_key.exchange(ephemeral_public_key)
        wrapping_key = ECCKeyWrapper._derive_key(shared_secret)

        nonce = bytes.fromhex(wrapped_data["nonce"])
        encrypted_key = bytes.fromhex(wrapped_data["encrypted_key"])

        aead = ChaCha20Poly1305(wrapping_key)

        return aead.decrypt(nonce, encrypted_key, None)
