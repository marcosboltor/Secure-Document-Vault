import json
from secure_document_vault.core.exceptions import IntegrityErrorException
from secure_document_vault.modules.randomness import RandomnessManager
from secure_document_vault.modules.vault_builder import VaultBuilder
from secure_document_vault.modules.key_wrapping import ECCKeyWrapper
from secure_document_vault.modules.aead import AEAD_Engine


def encriptar(
    archivo_en_bytes: bytes, nombre_archivo: str, recipients_info: list
) -> bytes:
    """
    Cifra un archivo en bytes y lo empaqueta en formato .vault.

    :param archivo_en_bytes: Archivo original en bytes.
    :param nombre_archivo: Nombre del archivo original.
    :param recipients_info: Lista de diccionarios [{"id": <str>,
                            "public_key": <X25519PublicKey>}, ...]
    :return: Archivo completo en formato .vault como bytes.
    """
    dev2_randomness = RandomnessManager()
    dev3_builder = VaultBuilder()

    file_key = dev2_randomness.generate_key()

    recipients_metadata = []
    for recipient in recipients_info:
        wrapped_data = ECCKeyWrapper.wrap_key(file_key, recipient["public_key"])
        recipients_metadata.append(
            {"id": recipient["id"], "encrypted_key": wrapped_data}
        )

    aad_bytes = dev3_builder.recolectar_metadatos(
        nombre_archivo, recipients=recipients_metadata
    )

    dev1_engine = AEAD_Engine(file_key)
    nonce_generado = dev2_randomness.generate_nonce()

    ciphertext = dev1_engine.encrypt(nonce_generado, archivo_en_bytes, aad_bytes)
    archivo_vault = dev3_builder.empaquetar(nonce_generado, aad_bytes, ciphertext)

    return archivo_vault


def desencriptar(archivo_vault: bytes, user_id: str, private_key) -> bytes:
    """
    Desempaqueta y descifra un archivo .vault.

    :param archivo_vault: Archivo en formato .vault en bytes.
    :param user_id: Identificador del usuario que intenta descifrar.
    :param private_key: Llave privada (X25519PrivateKey) del usuario.
    :return: Archivo original en bytes (texto plano).
    """
    dev3_builder = VaultBuilder()

    nonce_leido, aad_leido, ciphertext_leido = dev3_builder.desempaquetar(archivo_vault)

    try:
        metadatos = json.loads(aad_leido.decode("utf-8"))
    except json.JSONDecodeError:
        raise IntegrityErrorException("Metadatos AAD inválidos o corruptos.")

    recipients = metadatos.get("recipients", [])
    user_entry = next((r for r in recipients if r["id"] == user_id), None)

    if not user_entry:
        raise IntegrityErrorException(
            f"Usuario {user_id} no autorizado para este archivo."
        )

    try:
        file_key = ECCKeyWrapper.unwrap_key(user_entry["encrypted_key"], private_key)
    except Exception as e:
        raise IntegrityErrorException(f"Error al descifrar llave contenedora: {e}")

    dev1_engine = AEAD_Engine(file_key)
    mensaje_recuperado = dev1_engine.decrypt(nonce_leido, ciphertext_leido, aad_leido)

    return mensaje_recuperado
