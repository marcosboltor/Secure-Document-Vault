import os
import json
import uuid
import hashlib
import base64
from datetime import datetime, timezone
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidTag


class KeyProtector:
    """Manages password-based encryption of private keys.

    Uses PBKDF2 + ChaCha20-Poly1305.

    The keystore format includes:
    - Encrypted private key (ChaCha20-Poly1305 AEAD)
    - PBKDF2 salt and iteration count
    - Rich metadata: key_id, user_id, key_version, creation_date, encryption_algorithm
    - SHA-256 integrity checksum over encrypted payload + nonce + salt
    """

    KEYSTORE_VERSION = 1
    KDF_ITERATIONS = 600_000
    ENCRYPTION_ALGORITHM = "ChaCha20-Poly1305"
    KDF_ALGORITHM = "PBKDF2-HMAC-SHA256"

    # Fields required for a valid keystore
    REQUIRED_FIELDS = {
        "metadata",
        "kdf_parameters",
        "nonce",
        "encrypted_key",
        "checksum",
    }
    REQUIRED_METADATA = {
        "key_id",
        "user_id",
        "key_version",
        "creation_date",
        "encryption_algorithm",
    }
    REQUIRED_KDF = {"kdf_algorithm", "iterations", "salt"}

    @staticmethod
    def _compute_checksum(encrypted_key_b64: str, nonce_b64: str, salt_b64: str) -> str:
        """Compute SHA-256 checksum over the encrypted key, nonce, and salt."""
        payload = f"{encrypted_key_b64}:{nonce_b64}:{salt_b64}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def protect_key(password: str, private_key_obj, user_id: str = "unknown") -> dict:
        """Encrypt a private key with a password and return a keystore dictionary.

        The keystore includes full metadata and a SHA-256 integrity checksum
        so that corruption or tampering can be detected during restore.
        """
        # Convert key to raw PEM bytes
        private_key_bytes = private_key_obj.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Generate cryptographically secure random salt (128 bits)
        salt = os.urandom(16)

        # Derive KEK (Key Encryption Key) from user password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=KeyProtector.KDF_ITERATIONS,
        )
        kek = kdf.derive(password.encode("utf-8"))

        # Encrypt private key with ChaCha20-Poly1305
        nonce = os.urandom(12)
        chacha20 = ChaCha20Poly1305(kek)
        encrypted_key = chacha20.encrypt(nonce, private_key_bytes, None)

        # Encode to base64 for JSON serialization
        encrypted_key_b64 = base64.b64encode(encrypted_key).decode("utf-8")
        nonce_b64 = base64.b64encode(nonce).decode("utf-8")
        salt_b64 = base64.b64encode(salt).decode("utf-8")

        # Compute integrity checksum
        checksum = KeyProtector._compute_checksum(
            encrypted_key_b64, nonce_b64, salt_b64
        )

        return {
            "metadata": {
                "key_id": str(uuid.uuid4()),
                "user_id": user_id,
                "key_version": KeyProtector.KEYSTORE_VERSION,
                "creation_date": datetime.now(timezone.utc).isoformat(),
                "encryption_algorithm": KeyProtector.ENCRYPTION_ALGORITHM,
            },
            "kdf_parameters": {
                "kdf_algorithm": KeyProtector.KDF_ALGORITHM,
                "iterations": KeyProtector.KDF_ITERATIONS,
                "salt": salt_b64,
            },
            "nonce": nonce_b64,
            "encrypted_key": encrypted_key_b64,
            "checksum": checksum,
        }

    @staticmethod
    def verify_password(password: str, keystore_dict: dict):
        """Decrypt a private key from a keystore dictionary using the given password.

        Raises ValueError if the password is wrong or the keystore is corrupted.
        """
        salt = base64.b64decode(keystore_dict["kdf_parameters"]["salt"])
        nonce = base64.b64decode(keystore_dict["nonce"])
        encrypted_key = base64.b64decode(keystore_dict["encrypted_key"])
        iterations = keystore_dict["kdf_parameters"]["iterations"]

        # Re-derive the same KEK using password + recovered salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        kek = kdf.derive(password.encode("utf-8"))

        chacha = ChaCha20Poly1305(kek)

        try:
            recovered_key_bytes = chacha.decrypt(nonce, encrypted_key, None)
        except InvalidTag:
            raise ValueError("CONTRASEÑA INCORRECTA O KEYSTORE CORRUPTO")

        private_key_obj = serialization.load_pem_private_key(
            recovered_key_bytes, password=None
        )

        return private_key_obj

    @staticmethod
    def validate_keystore(keystore_dict: dict) -> tuple[bool, str]:
        """Validate keystore structural integrity and checksum.

        Returns (is_valid, reason). Does NOT require the password — this is
        a structural and integrity check only.
        """
        # Check it's a dict
        if not isinstance(keystore_dict, dict):
            return False, "Keystore must be a dictionary."

        # Check required top-level fields
        missing = KeyProtector.REQUIRED_FIELDS - set(keystore_dict.keys())
        if missing:
            return False, f"Missing required fields: {', '.join(sorted(missing))}"

        # Check metadata sub-fields
        metadata = keystore_dict.get("metadata", {})
        if not isinstance(metadata, dict):
            return False, "metadata must be a dictionary."
        missing_meta = KeyProtector.REQUIRED_METADATA - set(metadata.keys())
        if missing_meta:
            return False, f"Missing metadata fields: {', '.join(sorted(missing_meta))}"

        # Check KDF sub-fields
        kdf_params = keystore_dict.get("kdf_parameters", {})
        if not isinstance(kdf_params, dict):
            return False, "kdf_parameters must be a dictionary."
        missing_kdf = KeyProtector.REQUIRED_KDF - set(kdf_params.keys())
        if missing_kdf:
            return False, f"Missing KDF fields: {', '.join(sorted(missing_kdf))}"

        # Validate iteration count (reject dangerously low values)
        iterations = kdf_params.get("iterations", 0)
        if not isinstance(iterations, int) or iterations < 100_000:
            return False, f"Iterations too low ({iterations}). Minimum is 100,000."

        # Verify SHA-256 checksum
        expected_checksum = keystore_dict.get("checksum", "")
        computed_checksum = KeyProtector._compute_checksum(
            keystore_dict["encrypted_key"],
            keystore_dict["nonce"],
            kdf_params["salt"],
        )
        if expected_checksum != computed_checksum:
            return (
                False,
                "Checksum mismatch — keystore may be corrupted or tampered with.",
            )

        return True, "Valid."

    @staticmethod
    def export_keystore_bundle(
        enc_keystore: dict,
        sign_keystore: dict,
        user_name: str = "",
        user_email: str = "",
        user_id: str = "",
    ) -> dict:
        """Export a complete keystore bundle.

        Contains both encryption and signing keystores.

        The bundle format is 'vault-keystore-v1' and includes user metadata
        for identification purposes (no private key material).
        """
        return {
            "format": "vault-keystore-v1",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user": {
                "name": user_name,
                "email": user_email,
                "id": user_id,
            },
            "keystores": {
                "encryption": enc_keystore,
                "signing": sign_keystore,
            },
        }

    @staticmethod
    def import_keystore_bundle(bundle_dict: dict) -> tuple[bool, str, dict | None]:
        """Validate and import a keystore bundle.

        Returns (is_valid, reason, keystores_or_none).
        Validates format version, structure, and integrity of both keystores.
        """
        if not isinstance(bundle_dict, dict):
            return False, "Bundle must be a dictionary.", None

        # Check format version
        fmt = bundle_dict.get("format")
        if fmt != "vault-keystore-v1":
            return False, f"Unknown or missing format: {fmt}", None

        # Check keystores container
        keystores = bundle_dict.get("keystores")
        if not isinstance(keystores, dict):
            return False, "Missing 'keystores' container.", None

        # Validate each keystore
        for key_name in ("encryption", "signing"):
            ks = keystores.get(key_name)
            if not isinstance(ks, dict):
                return False, f"Missing or invalid '{key_name}' keystore.", None

            valid, reason = KeyProtector.validate_keystore(ks)
            if not valid:
                return False, f"{key_name} keystore: {reason}", None

        return True, "Valid.", keystores

    @staticmethod
    def backup_keystore(keystore_dict: dict, filepath: str) -> None:
        """Write a keystore dictionary to a local file as JSON."""
        dirname = os.path.dirname(filepath)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(keystore_dict, f, indent=4)

    @staticmethod
    def restore_keystore(filepath: str) -> dict:
        """Read a keystore JSON file from disk and return the dictionary."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"El archivo de keystore no existe: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
