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

        from cryptography.hazmat.primitives import serialization

        ephemeral_pub_bytes = ephemeral_public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )

        return {
            "ephemeral_pub": ephemeral_pub_bytes.hex(),
            "nonce": nonce.hex(),
            "encrypted_key": encrypted_key.hex(),
        }

    @staticmethod
    def unwrap_key(wrapped_data: dict, recipient_private_key) -> bytes:
        required_fields = ("ephemeral_pub", "nonce", "encrypted_key")
        for field in required_fields:
            if field not in wrapped_data:
                raise ValueError(
                    f"Entrada de destinatario invalida: falta '{field}'."
                )
            if not isinstance(wrapped_data[field], str):
                raise ValueError(
                    f"Campo '{field}' debe ser una cadena hexadecimal."
                )
            try:
                bytes.fromhex(wrapped_data[field])
            except ValueError:
                raise ValueError(
                    f"Campo '{field}' contiene datos no hexadecimales."
                )

        ephemeral_pub_bytes = bytes.fromhex(wrapped_data["ephemeral_pub"])
        if len(ephemeral_pub_bytes) != 32:
            raise ValueError(
                f"ephemeral_pub invalido: esperados 32 bytes, "
                f"recibidos {len(ephemeral_pub_bytes)}."
            )

        nonce_bytes = bytes.fromhex(wrapped_data["nonce"])
        if len(nonce_bytes) != 12:
            raise ValueError(
                f"nonce invalido: esperados 12 bytes, "
                f"recibidos {len(nonce_bytes)}."
            )

        ephemeral_public_key = x25519.X25519PublicKey.from_public_bytes(
            ephemeral_pub_bytes
        )
        shared_secret = recipient_private_key.exchange(ephemeral_public_key)
        wrapping_key = ECCKeyWrapper._derive_key(shared_secret)

        encrypted_key = bytes.fromhex(wrapped_data["encrypted_key"])
        aead = ChaCha20Poly1305(wrapping_key)

        return aead.decrypt(nonce_bytes, encrypted_key, None)
