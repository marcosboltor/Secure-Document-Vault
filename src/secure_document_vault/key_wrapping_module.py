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
        """
        Derive a secure symmetric key from the shared secret using HKDF.

        :param shared_secret: Result of the ECDH key exchange
        :return: 32-byte symmetric key
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=None,
            info=b"file-key-wrap",
        )
        return hkdf.derive(shared_secret)

    @staticmethod
    def wrap_key(file_key: bytes, recipient_public_key) -> dict:
        """
        Encrypt (wrap) the file_key using the recipient's public key.

        :param file_key: Symmetric key (32 bytes) used to encrypt the file
        :param recipient_public_key: Recipient's X25519 public key
        :return: Dictionary containing wrapped key data
        """

        # Generate ephemeral key pair
        ephemeral_private_key = x25519.X25519PrivateKey.generate()
        ephemeral_public_key = ephemeral_private_key.public_key()

        # Perform ECDH to compute shared secret
        shared_secret = ephemeral_private_key.exchange(recipient_public_key)

        # Derive a symmetric wrapping key from the shared secret
        wrapping_key = ECCKeyWrapper._derive_key(shared_secret)

        # Encrypt the file_key using AEAD
        nonce = secrets.token_bytes(12)  # 96-bit nonce
        aead = ChaCha20Poly1305(wrapping_key)
        encrypted_key = aead.encrypt(nonce, file_key, None)

        # Serialize ephemeral public key (raw 32 bytes)
        ephemeral_pub_bytes = ephemeral_public_key.public_bytes_raw()

        return {
            "ephemeral_pub": ephemeral_pub_bytes.hex(),
            "nonce": nonce.hex(),
            "encrypted_key": encrypted_key.hex(),
        }

    @staticmethod
    def unwrap_key(wrapped_data: dict, recipient_private_key) -> bytes:
        """
        Decrypt (unwrap) the file_key using the recipient's private key.

        :param wrapped_data: Dictionary returned by wrap_key
        :param recipient_private_key: Recipient's X25519 private key
        :return: Original file_key
        """

        # Reconstruct ephemeral public key from stored data
        ephemeral_pub_bytes = bytes.fromhex(wrapped_data["ephemeral_pub"])
        ephemeral_public_key = x25519.X25519PublicKey.from_public_bytes(
            ephemeral_pub_bytes
        )

        # Perform ECDH to compute shared secret
        shared_secret = recipient_private_key.exchange(ephemeral_public_key)

        # 3. Derive the same symmetric wrapping key
        wrapping_key = ECCKeyWrapper._derive_key(shared_secret)

        # 4. Decrypt the file_key
        nonce = bytes.fromhex(wrapped_data["nonce"])
        encrypted_key = bytes.fromhex(wrapped_data["encrypted_key"])

        aead = ChaCha20Poly1305(wrapping_key)

        return aead.decrypt(nonce, encrypted_key, None)
