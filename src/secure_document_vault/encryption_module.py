import json
import secrets
import struct
import time
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.exceptions import InvalidTag

from .key_wrapping_module import ECCKeyWrapper

# Dev 1 Sebastian
class IntegrityErrorException(Exception):
    pass


class AEAD_Engine:
    def __init__(self, key: bytes):
        """Inicializa el motor criptográfico.

        :param key: La llave simetrica de 256 bits generada.
        """
        self.chacha20 = ChaCha20Poly1305(key)

    def encrypt(self, nonce: bytes, plaintext: bytes, aad: bytes) -> bytes:
        """
        Encripta los datos y los vincula con los metadatos

        :param nonce: Un valor de uso único en bytes.
        :param plaintext: El contenido del archivo original en bytes.
        :param aad: Los metadatos asociados en bytes.
        :return: El texto cifrado en bytes (incluye etiqueta de autenticación).
        """
        ciphertext = self.chacha20.encrypt(nonce, plaintext, aad)
        return ciphertext

    def decrypt(self, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
        """
        Descifra los datos y verifica su integridad/authenticidad.

        :param nonce: El mismo nonce usado para cifrar.
        :param ciphertext: El texto cifrado en bytes.
        :param aad: Los mismos metadatos usados para cifrar.
        :return: El texto original en bytes.
        """
        try:
            plaintext = self.chacha20.decrypt(nonce, ciphertext, aad)
            return plaintext
        except InvalidTag:
            message = (
                "ALERTA DE SEGURIDAD: El archivo o los metadatos han sido modificados "
                "o la llave es incorrecta"
            )
            print(f">>>> ERROR: {message} >>>>")
            raise IntegrityErrorException(message)


# Dev 2 Daniel
class RandomnessManager:

    @staticmethod
    def generate_key(length: int = 32) -> bytes:
        """
        Genera una llave simétrica fresca de la longitud especificada
        (por defecto 256 bits = 32 bytes).
        Utiliza secrets.token_bytes el cual está ligado al CSPRNG interno del SO.

        :param length: Longitud de la llave en bytes.
        :return: Bytes aleatorios criptográficamente seguros para la llave.
        """
        return secrets.token_bytes(length)

    @staticmethod
    def generate_nonce(length: int = 12) -> bytes:
        """
        Genera un nonce aleatorio criptográficamente seguro.
        El valor por defecto es de 12 bytes, que es el estándar para los algoritmos
        ChaCha20-Poly1305 y AES-GCM.
        Utiliza secrets.token_bytes para garantizar imprevisibilidad y evitar
        repeticiones.

        :param length: Longitud del nonce en bytes.
        :return: Bytes aleatorios criptográficamente seguros para el nonce.
        """
        return secrets.token_bytes(length)


# Dev 3 Marcos
class VaultBuilder:
    def __init__(self):
        # Header de 8 bytes para validar que es nuestro archivo
        self.magic_header = b"VAULT10\x00"

    def recolectar_metadatos(
        self,
        nombre_archivo,
        recipients=None,
        algoritmo="ChaCha20-Poly1305",
        parametros_extra=None,
    ):
        """Recolecta y serializa los metadatos a bytes (AAD)."""
        metadatos = {
            "file_name": nombre_archivo,
            "recipients": recipients or [],
            "version": "1.0.0",
            "algorithm": algoritmo,
            "timestamp": int(time.time()),
            "params": parametros_extra or {},
        }
        return json.dumps(metadatos).encode("utf-8")

    def empaquetar(
        self, nonce: bytes, aad_metadatos: bytes, ciphertext_con_tag: bytes
    ) -> bytes:
        """Empaqueta los componentes en el formato .vault"""
        longitud_metadatos = struct.pack("<I", len(aad_metadatos))

        # Concatenamos todo
        archivo_vault_final = (
            self.magic_header
            + nonce
            + longitud_metadatos
            + aad_metadatos
            + ciphertext_con_tag
        )
        return archivo_vault_final

    def desempaquetar(self, vault_bytes: bytes):
        """Lee el archivo .vault y separa sus componentes para que Dev 1 pueda
        descifrar.
        """
        header = vault_bytes[:8]
        if header != self.magic_header:
            raise ValueError("Archivo no válido o corrupto: Header incorrecto.")
        nonce = vault_bytes[8:20]
        longitud_metadatos_bytes = vault_bytes[20:24]
        longitud_metadatos = struct.unpack("<I", longitud_metadatos_bytes)[0]
        inicio_aad = 24
        fin_aad = 24 + longitud_metadatos
        aad_metadatos = vault_bytes[inicio_aad:fin_aad]
        ciphertext_con_tag = vault_bytes[fin_aad:]

        return nonce, aad_metadatos, ciphertext_con_tag


# Dev 2 FUNCION UNICA CON INTEGRACION COMPLETA:


def encriptar(archivo_en_bytes: bytes, nombre_archivo: str, recipients_info: list) -> bytes:
    """
    Cifra un archivo en bytes y lo empaqueta en formato .vault.

    :param archivo_en_bytes: Archivo original en bytes.
    :param nombre_archivo: Nombre del archivo original.
    :param recipients_info: Lista de diccionarios [{"id": <str>, "public_key": <X25519PublicKey>}, ...]
    :return: Archivo completo en formato .vault como bytes.
    """
    dev2_randomness = RandomnessManager()
    dev3_builder = VaultBuilder()

    # 1. Generate a symmetric file key
    file_key = dev2_randomness.generate_key()

    # 2. Encrypt the file key using each recipient's public key
    recipients_metadata = []
    for recipient in recipients_info:
        wrapped_data = ECCKeyWrapper.wrap_key(file_key, recipient["public_key"])
        recipients_metadata.append({
            "id": recipient["id"],
            "encrypted_key": wrapped_data
        })

    # Recolectamos metadatos ligando a los recipients para AAD
    aad_bytes = dev3_builder.recolectar_metadatos(nombre_archivo, recipients=recipients_metadata)

    # Inicializamos el motor ChaCha20 y generamos nonce
    dev1_engine = AEAD_Engine(file_key)
    nonce_generado = dev2_randomness.generate_nonce()

    # Ciframos el archivo usando el Symmetric Key
    ciphertext = dev1_engine.encrypt(nonce_generado, archivo_en_bytes, aad_bytes)

    # Empaquetamos en .vault
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

    # Desempaquetamos los componentes
    nonce_leido, aad_leido, ciphertext_leido = dev3_builder.desempaquetar(archivo_vault)

    # Analizamos los metadatos para encontrar la llave de este usuario
    try:
        metadatos = json.loads(aad_leido.decode("utf-8"))
    except json.JSONDecodeError:
        raise IntegrityErrorException("Metadatos AAD inválidos o corruptos.")

    recipients = metadatos.get("recipients", [])
    user_entry = next((recipient for recipient in recipients if recipient["id"] == user_id), None)

    if not user_entry:
        raise IntegrityErrorException(f"Usuario {user_id} no autorizado para este archivo.")

    # Desenvolvemos (unwrap) el Symmetric Key usando la llave privada
    try:
        file_key = ECCKeyWrapper.unwrap_key(user_entry["encrypted_key"], private_key)
    except Exception as e:
        raise IntegrityErrorException(f"Error al descifrar llave contenedora: {e}")

    # Desciframos el ciphertext principal
    dev1_engine = AEAD_Engine(file_key)
    mensaje_recuperado = dev1_engine.decrypt(nonce_leido, ciphertext_leido, aad_leido)

    return mensaje_recuperado


def main():
    from cryptography.hazmat.primitives.asymmetric import x25519
    # Ejemplo de uso
    alice_private = x25519.X25519PrivateKey.generate()
    alice_public = alice_private.public_key()

    bob_private = x25519.X25519PrivateKey.generate()
    bob_public = bob_private.public_key()

    recipients = [
        {"id": "alice", "public_key": alice_public},
        {"id": "bob", "public_key": bob_public}
    ]

    nombre_archivo = "secreto.txt"
    archivo_original = b"Este es un secreto super importante de la empresa."
    archivo_cifrado = encriptar(archivo_original, nombre_archivo, recipients)
    
    # Alice intenta descifrar
    archivo_descifrado_alice = desencriptar(archivo_cifrado, "alice", alice_private)
    print(f"Alice recupero: {archivo_descifrado_alice}")

    # Bob intenta descifrar
    archivo_descifrado_bob = desencriptar(archivo_cifrado, "bob", bob_private)
    print(f"Bob recupero: {archivo_descifrado_bob}")


if __name__ == "__main__":
    main()
