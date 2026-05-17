import os
import json
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidTag


class KeyProtector:
    @staticmethod
    def protect_key(password: str, private_key_obj, user_id: str = "unknown"):
        """Cifra una llave privada usando una contraseña y devuelve
        un diccionario"""
        # Convertir llave a bytes crudos
        private_key_bytes = private_key_obj.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Generar un salt pseudo aleatorio criptograficamente seguro
        # de 128 bits
        salt = os.urandom(16)

        # Derivar la KEK (Key Encryption key) de la contraseña del usuario
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # Llave de 256 bits
            salt=salt,
            iterations=600_000
        )
        kek = kdf.derive(password.encode('utf-8'))

        # Cifrar llave con bytes de llave usando ChaCha20
        nonce = os.urandom(12)
        chacha20 = ChaCha20Poly1305(kek)
        encrypted_key = chacha20.encrypt(nonce, private_key_bytes, None)

        return {
            "metadata": {
                "user_id": user_id,
                "description": "Encrypted Private Key"
            },
            "kdf_parameters": {
                "kdf_algorithm": "PBDKF2-HMAC-SHA256",
                "iterations": 600_000,
                "salt": base64.b64encode(salt).decode('utf-8')
            },
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "encrypted_key": base64.b64encode(encrypted_key).decode('utf-8')
        }

    @staticmethod
    def verify_password(password: str, keystore_dict: dict):
        salt = base64.b64decode(keystore_dict["kdf_parameters"]["salt"])
        nonce = base64.b64decode(keystore_dict["nonce"])
        encrypted_key = base64.b64decode(keystore_dict["encrypted_key"])
        iterations = keystore_dict["kdf_parameters"]["iterations"]

        # Re-derivar la misma KEK empleando la contraseña y salt recuperado
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # Llave dde 256 bits
            salt=salt,
            iterations=iterations
        )

        kek = kdf.derive(password.encode('utf-8'))

        chacha = ChaCha20Poly1305(kek)

        try:
            # Descifrar llave privada con el nonce y la llave cifrada
            recovered_key_bytes = chacha.decrypt(nonce, encrypted_key, None)
        except InvalidTag:
            raise ValueError("CONTRASEÑA INCORRECTA O KEYSTORE CORRUPTO")

        private_key_obj = serialization.load_pem_private_key(
            recovered_key_bytes,
            password=None
        )

        return private_key_obj

    @staticmethod
    def backup_keystore(keystore_dict: dict, filepath: str) -> None:
        """
        Escribe el diccionario de Keystore en un archivo local usando json.dump.
        """
        dirname = os.path.dirname(filepath)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(keystore_dict, f, indent=4)

    @staticmethod
    def restore_keystore(filepath: str) -> dict:
        """
        Lee un archivo .keystore (o JSON) desde el disco usando json.load
        y retorna el diccionario para el KeyProtector.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"El archivo de keystore no existe: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
