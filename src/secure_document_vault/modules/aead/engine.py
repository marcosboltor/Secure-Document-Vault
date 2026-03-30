from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.exceptions import InvalidTag
from secure_document_vault.core.exceptions import IntegrityErrorException


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
