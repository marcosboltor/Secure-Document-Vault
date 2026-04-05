from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization


class KeyManager:
    def __init__(self):
        """Initializes KeyManager with empty dictionaries to store keys."""
        self.__db_public_keys = {}
        self.__db_private_keys = {}

    def generate_keys_for_user(self, user_id: str):
        """
        Generates a pair of X25519 keys for a user.
        Private key for signing, public key for encryption.
        """
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()

        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        self.__db_public_keys[user_id] = pem_public
        self.__db_private_keys[user_id] = pem_private

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
