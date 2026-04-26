import json
from secure_document_vault.core.exceptions import IntegrityErrorException
from secure_document_vault.modules.randomness import RandomnessManager
from secure_document_vault.modules.vault_builder import VaultBuilder
from secure_document_vault.modules.key_wrapping import ECCKeyWrapper
from secure_document_vault.modules.aead import AEAD_Engine
from cryptography.hazmat.primitives.asymmetric import ed25519
from secure_document_vault.modules.signing.signer import DocumentSigner


def encriptar(
    archivo_en_bytes: bytes,
    nombre_archivo: str,
    recipients_info: list,
    signer_id: str,
    signer_private_key: ed25519.Ed25519PrivateKey
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
        signer_fingerprint=fingerprint
    )

    # Generar Nonce y cifrar
    dev1_engine = AEAD_Engine(file_key)
    nonce_generado = dev2_randomness.generate_nonce()
    ciphertext = dev1_engine.encrypt(nonce_generado,
                                     archivo_en_bytes, aad_bytes)

    # Firmar datos (AAD y Ciphertext)
    data_to_sign = aad_bytes + ciphertext
    sign = DocumentSigner.sign(signer_private_key, data_to_sign)

    archivo_vault = dev3_builder.empaquetar(
        nonce=nonce_generado,
        aad_metadatos=aad_bytes,
        ciphertext_con_tag=ciphertext,
        signature=sign
    )

    return archivo_vault


def desencriptar(archivo_vault: bytes,
                 user_id: str,
                 private_key,
                 signer_public_key: ed25519.Ed25519PrivateKey) -> bytes:
    """
    Verifica la firma, desempaqueta y descifra un archivo .vault.

    :param archivo_vault: Archivo en formato .vault en bytes.
    :param user_id: Identificador del usuario que intenta descifrar.
    :param private_key: Llave privada (X25519PrivateKey) del usuario.
    :signer_public_key: Llave publica del usuario que firmó el archivo
    :return: Archivo original en bytes (texto plano).
    """
    dev3_builder = VaultBuilder()

    result = dev3_builder.desempaquetar(archivo_vault)

    # Verificar que el contenedor tenga firma digital
    if len(result) == 4:
        nonce, aad, ciphertext, signature = result
    else:
        raise IntegrityErrorException("El archivo no contiene una firma digital.")

    data_signed = aad + ciphertext

    # Verificar la firma primero
    try:
        DocumentSigner.verify(signer_public_key, data_signed, signature)
    except Exception:
        raise IntegrityErrorException("ALERTA: Firma digital inválida.")

    # Leer los AAD y validar acceso
    try:
        metadatos = json.loads(aad.decode("utf-8"))
    except json.JSONDecodeError:
        raise IntegrityErrorException("Metadatos AAD inválidos o corruptos.")

    recipients = metadatos.get("recipients", [])
    user_entry = next((r for r in recipients if r["id"] == user_id), None)

    if not user_entry:
        raise IntegrityErrorException(f"""Usuario {user_id} no autorizado
                                      para este archivo.""")

    # Desenvolver la llave y descifrar
    try:
        file_key = ECCKeyWrapper.unwrap_key(user_entry["encrypted_key"], private_key)
    except Exception as e:
        raise IntegrityErrorException(f"Error al descifrar llave contenedora: {e}")

    dev1_engine = AEAD_Engine(file_key)
    mensaje_recuperado = dev1_engine.decrypt(nonce, ciphertext, aad)

    return mensaje_recuperado
