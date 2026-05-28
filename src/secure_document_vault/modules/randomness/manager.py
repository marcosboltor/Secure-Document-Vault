import secrets


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
