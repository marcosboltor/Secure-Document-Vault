import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature


class DocumentSigner:
    """Módulo de firma digital basado en Ed25519.

    Proporciona generación de claves, firma y verificación de datos,
    así como generación de fingerprints para identificación de firmantes.
    """

    @staticmethod
    def generate_key_pair():
        """Genera un par de claves Ed25519 (privada, pública).

        :return: Tupla (Ed25519PrivateKey, Ed25519PublicKey).
        """
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def get_fingerprint(public_key: Ed25519PublicKey) -> str:
        """Calcula el fingerprint SHA-256 de una clave pública Ed25519.

        :param public_key: Clave pública Ed25519.
        :return: Fingerprint como string hexadecimal (64 caracteres).
        """
        raw_bytes = public_key.public_bytes_raw()
        return hashlib.sha256(raw_bytes).hexdigest()

    @staticmethod
    def sign(private_key: Ed25519PrivateKey, data: bytes) -> bytes:
        """Firma datos usando la clave privada Ed25519.

        Ed25519 internamente aplica SHA-512 sobre los datos antes de firmar,
        por lo que no es necesario hacer hashing manual previo.

        :param private_key: Clave privada Ed25519 del firmante.
        :param data: Datos a firmar (metadata AAD + ciphertext).
        :return: Firma digital de 64 bytes.
        """
        return private_key.sign(data)

    @staticmethod
    def verify(public_key: Ed25519PublicKey, data: bytes, signature: bytes) -> bool:
        """Verifica una firma digital usando la clave pública Ed25519.

        :param public_key: Clave pública Ed25519 del firmante.
        :param data: Datos originales que fueron firmados.
        :param signature: Firma digital a verificar (64 bytes).
        :return: True si la firma es válida.
        :raises InvalidSignature: Si la firma no es válida.
        """
        public_key.verify(signature, data)
        return True
