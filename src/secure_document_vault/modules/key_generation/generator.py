from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives import serialization
from secure_document_vault.modules.key_store.generator import KeyProtector


class KeyManager:
    def __init__(self):
        """Initializes KeyManager with empty dictionaries to store keys."""
        self.__db_public_keys = {}
        self.__db_private_keys = {}
        self.__db_signing_public_keys = {}
        self.__db_signing_private_keys = {}

    def generate_keys_for_user(self, user_id: str, password: str):
        """
        Generates a pair of X25519 keys for encryption and
        a pair of Ed25519 keys for signing.
        """
        # 1. Encryption Keys (X25519)
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()

        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        self.__db_public_keys[user_id] = pem_public
        self.__db_private_keys[user_id] = KeyProtector.protect_key(
            password, private_key, user_id
        )

        # 2. Signing Keys (Ed25519)
        signing_private = ed25519.Ed25519PrivateKey.generate()
        signing_public = signing_private.public_key()

        pem_signing_public = signing_public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        self.__db_signing_public_keys[user_id] = pem_signing_public
        self.__db_signing_private_keys[user_id] = KeyProtector.protect_key(
            password, signing_private, user_id
        )

    def get_public_key(self, user_id: str):
        """
        Retrieves the public key for a given user ID.
        """
        if user_id not in self.__db_public_keys:
            raise ValueError(f"Public key for user ID {user_id} not found.")
        return self.__db_public_keys[user_id]

    def get_private_key(self, user_id: str):
        if user_id not in self.__db_private_keys:
            raise ValueError(f"Private key for user ID {user_id} not found.")
        return self.__db_private_keys[user_id]

    def get_signing_public_key(self, user_id: str):
        if user_id not in self.__db_signing_public_keys:
            raise ValueError(f"Signing public key for user ID {user_id} not found.")
        return self.__db_signing_public_keys[user_id]

    def get_signing_private_key(self, user_id: str):
        if user_id not in self.__db_signing_private_keys:
            raise ValueError(f"Signing private key for user ID {user_id} not found.")
        return self.__db_signing_private_keys[user_id]
