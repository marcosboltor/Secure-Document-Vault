import json
from secure_document_vault.core.exceptions import IntegrityErrorException
from secure_document_vault.modules.randomness import RandomnessManager
from secure_document_vault.modules.vault_builder import VaultBuilder
from secure_document_vault.modules.key_wrapping import ECCKeyWrapper
from secure_document_vault.modules.aead import AEAD_Engine
from cryptography.hazmat.primitives.asymmetric import ed25519
from secure_document_vault.modules.signing.signer import DocumentSigner
import hmac


def encriptar(
    archivo_en_bytes: bytes,
    nombre_archivo: str,
    recipients_info: list,
    signer_id: str,
    signer_private_key: ed25519.Ed25519PrivateKey,
) -> bytes:
    """
    Cifra un archivo en bytes, lo firma digitalmente y
    empaqueta en formato .vault.

    :param archivo_en_bytes: Archivo original en bytes.
    :param nombre_archivo: Nombre del archivo original.
    :param recipients_info: Lista de diccionarios [{"id": <str>,
                            "public_key": <X25519PublicKey>}, ...]
    :param signer_id: ID del usuario que firma el archivo
    :param signer_private_key: Llave privada para firmar el archivo
    :return: Archivo completo en formato .vault como bytes.
    """
    dev2_randomness = RandomnessManager()
    dev3_builder = VaultBuilder()

    # Obtener identidad del firmante
    signer_pub = signer_private_key.public_key()
    fingerprint = DocumentSigner.get_fingerprint(signer_pub)

    # Generar llave simetrica y envolverla
    file_key = dev2_randomness.generate_key()
    recipients_metadata = []
    for recipient in recipients_info:
        wrapped_data = ECCKeyWrapper.wrap_key(file_key, recipient["public_key"])
        recipients_metadata.append(
            {"id": recipient["id"], "encrypted_key": wrapped_data}
        )

    # Recolectar Metadatos (AAD) incluyendo datos del firmante
    aad_bytes = dev3_builder.recolectar_metadatos(
        nombre_archivo,
        recipients=recipients_metadata,
        signer_id=signer_id,
        signer_fingerprint=fingerprint,
    )

    # Generar Nonce y cifrar
    dev1_engine = AEAD_Engine(file_key)
    nonce_generado = dev2_randomness.generate_nonce()
    ciphertext = dev1_engine.encrypt(nonce_generado, archivo_en_bytes, aad_bytes)

    # Firmar datos (AAD y Ciphertext)
    data_to_sign = aad_bytes + ciphertext
    sign = DocumentSigner.sign(signer_private_key, data_to_sign)

    archivo_vault = dev3_builder.empaquetar(
        nonce=nonce_generado,
        aad_metadatos=aad_bytes,
        ciphertext_con_tag=ciphertext,
        signature=sign,
    )

    return archivo_vault


def _verificar_firma(signer_public_key, data_signed, signature):
    """Verifica la firma en los bytes crudos antes de procesar nada."""
    try:
        DocumentSigner.verify(signer_public_key, data_signed, signature)
    except Exception:
        raise IntegrityErrorException("ALERTA: Firma digital inválida.")


def _verificar_fingerprint(signer_public_key, metadatos):
    """Verifica que el fingerprint coincida para evitar suplantación."""
    signer_info = metadatos.get("signer")
    if signer_info:
        expected_fingerprint = signer_info.get("fingerprint", "")
        actual_fingerprint = DocumentSigner.get_fingerprint(signer_public_key)
        if not hmac.compare_digest(expected_fingerprint, actual_fingerprint):
            raise IntegrityErrorException(
                "ALERTA: El fingerprint del firmante no coincide con la "
                "clave pública proporcionada. Posible sustitución de identidad."
            )


def _parsear_metadatos(aad: bytes):
    """Intenta parsear los metadatos de forma segura."""
    try:
        return json.loads(aad.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Atrapamos UnicodeDecodeError por si el atacante corrompió los bytes
        raise IntegrityErrorException("Metadatos AAD inválidos o corruptos.")


def _validar_y_obtener_llave(metadatos, user_id, private_key):
    """Función auxiliar para validar acceso y obtener la llave del archivo."""
    recipients = metadatos.get("recipients", [])
    user_entry = next((r for r in recipients if r["id"] == user_id), None)

    if not user_entry:
        raise IntegrityErrorException(
            f"Usuario {user_id} no autorizado para este archivo."
        )

    try:
        return ECCKeyWrapper.unwrap_key(user_entry["encrypted_key"], private_key)
    except Exception as e:
        raise IntegrityErrorException(f"Error al descifrar llave contenedora: {e}")


def desencriptar(
    archivo_vault: bytes,
    user_id: str,
    private_key,
    signer_public_key: ed25519.Ed25519PublicKey,
) -> bytes:
    """
    Verifica la firma, desempaqueta y descifra un archivo .vault.
    """
    dev3_builder = VaultBuilder()
    result = dev3_builder.desempaquetar(archivo_vault)

    # Verificar que el contenedor tenga firma digital
    if len(result) != 4:
        raise IntegrityErrorException("El archivo no contiene una firma digital.")

    nonce, aad, ciphertext, signature = result

    # 1. VERIFICAR FIRMA PRIMERO (En bytes crudos, protección máxima)
    data_signed = aad + ciphertext
    _verificar_firma(signer_public_key, data_signed, signature)

    # 2. PARSEAR Y VERIFICAR FINGERPRINT (Solo si la firma fue válida)
    metadatos = _parsear_metadatos(aad)
    _verificar_fingerprint(signer_public_key, metadatos)

    # 3. VALIDAR USUARIO Y OBTENER LLAVE
    file_key = _validar_y_obtener_llave(metadatos, user_id, private_key)

    # 4. DESCIFRAR
    dev1_engine = AEAD_Engine(file_key)
    mensaje_recuperado = dev1_engine.decrypt(nonce, ciphertext, aad)

    return mensaje_recuperado
