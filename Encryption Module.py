import json, struct, time, os, secrets
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.exceptions import InvalidTag

#Dev 1 Sebastian
class IntegrityErrorException(Exception):
    pass

class AEAD_Engine:
    def __init__(self, key: bytes):
        '''Inicializa el motor criptográfico.

        :param key: La llave simetrica de 256 bits generada.
        '''
        self.chacha20 = ChaCha20Poly1305(key)

    def encrypt(self, nonce: bytes, plaintext: bytes, aad: bytes) -> bytes:
        '''
        Encripta los datos y los vincula con los metadatos

        :param nonce: Un valor de uso único en bytes. 
        :param plaintext: El contenido del archivo original en bytes. 
        :param aad: Los metadatos asociados en bytes. 
        :return: El texto cifrado en bytes (ya que incluye la etiqueta de autenticación).
        '''
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
            message = "ALERTA DE SEGURIDAD: El archivo o los metadatos han sido modificados o la llave es incorrecta"
            print(f">>>> ERROR: {message} >>>>")
            raise IntegrityErrorException(message)

#Dev 2 Daniel
class RandomnessManager:
    
    @staticmethod
    def generate_key(length: int = 32) -> bytes:
        """
        Genera una llave simétrica fresca de la longitud especificada (por defecto 256 bits = 32 bytes).
        Utiliza secrets.token_bytes el cual está ligado al CSPRNG interno del SO.
        
        :param length: Longitud de la llave en bytes.
        :return: Bytes aleatorios criptográficamente seguros para la llave.
        """
        return secrets.token_bytes(length)
        
    @staticmethod
    def generate_nonce(length: int = 12) -> bytes:
        """
        Genera un nonce aleatorio criptográficamente seguro.
        El valor por defecto es de 12 bytes, que es el estándar para los algoritmos ChaCha20-Poly1305 y AES-GCM.
        Utiliza secrets.token_bytes para garantizar imprevisibilidad y evitar repeticiones.
        
        :param length: Longitud del nonce en bytes.
        :return: Bytes aleatorios criptográficamente seguros para el nonce.
        """
        return secrets.token_bytes(length)

#Dev 3 Marcos
class VaultBuilder:
    def __init__(self):
        # Header de 8 bytes para validar que es nuestro archivo
        self.magic_header = b'VAULT10\x00'

    def recolectar_metadatos(self, nombre_archivo, algoritmo="ChaCha20-Poly1305", parametros_extra=None):
        """Recolecta y serializa los metadatos a bytes (AAD)."""
        metadatos = {
            "file_name": nombre_archivo,
            "version": "1.0.0",
            "algorithm": algoritmo,
            "timestamp": int(time.time()),
            "params": parametros_extra or {}
        }
        return json.dumps(metadatos).encode('utf-8')

    def empaquetar(self, nonce: bytes, aad_metadatos: bytes, ciphertext_con_tag: bytes) -> bytes:
        """Empaqueta los componentes en el formato .vault"""
        longitud_metadatos = struct.pack('<I', len(aad_metadatos))

        # Concatenamos todo
        archivo_vault_final = (
            self.magic_header +
            nonce +                 
            longitud_metadatos +    
            aad_metadatos +         
            ciphertext_con_tag      
        )
        return archivo_vault_final

    def desempaquetar(self, vault_bytes: bytes):
        """Lee el archivo .vault y separa sus componentes para que Dev 1 pueda descifrar."""
        header = vault_bytes[:8]
        if header != self.magic_header:
            raise ValueError("Archivo no válido o corrupto: Header incorrecto.")
        nonce = vault_bytes[8:20]
        longitud_metadatos_bytes = vault_bytes[20:24]
        longitud_metadatos = struct.unpack('<I', longitud_metadatos_bytes)[0] 
        inicio_aad = 24
        fin_aad = 24 + longitud_metadatos
        aad_metadatos = vault_bytes[inicio_aad:fin_aad]
        ciphertext_con_tag = vault_bytes[fin_aad:]

        return nonce, aad_metadatos, ciphertext_con_tag

#Dev 2 FUNCION UNICA CON INTEGRACION COMPLETA:

def encriptar(key: bytes, archivo_en_bytes: bytes, nombre_archivo: str) -> bytes:
    """
    Cifra un archivo en bytes y lo empaqueta en formato .vault.
    
    :param key: Llave simétrica de 256 bits (32 bytes).
    :param archivo_en_bytes: Archivo original en bytes.
    :param nombre_archivo: Nombre del archivo original.
    :return: Archivo completo en formato .vault como bytes.
    """
    dev1_engine = AEAD_Engine(key)
    dev2_randomness = RandomnessManager()
    dev3_builder = VaultBuilder()

    # Recolectamos metadatos (usando un nombre genérico para compatibilidad)
    aad_bytes = dev3_builder.recolectar_metadatos(nombre_archivo)
    
    # Generamos un nonce fresco para cada cifrado
    nonce_generado = dev2_randomness.generate_nonce()
    
    # Ciframos los datos
    ciphertext = dev1_engine.encrypt(nonce_generado, archivo_en_bytes, aad_bytes)
    
    # Empaquetamos todo en el formato final
    archivo_vault = dev3_builder.empaquetar(nonce_generado, aad_bytes, ciphertext)
    
    return archivo_vault


def desencriptar(key: bytes, archivo_vault: bytes) -> bytes:
    """
    Desempaqueta y descifra un archivo .vault devolviendo sus bytes originales.
    
    :param key: Llave simétrica de 256 bits (32 bytes) original.
    :param archivo_vault: Archivo en formato .vault en bytes.
    :return: Archivo original en bytes (texto plano).
    """
    dev1_engine = AEAD_Engine(key)
    dev3_builder = VaultBuilder()
    
    # Desempaquetamos los componentes
    nonce_leido, aad_leido, ciphertext_leido = dev3_builder.desempaquetar(archivo_vault)
    
    # Desciframos y validamos la integridad
    mensaje_recuperado = dev1_engine.decrypt(nonce_leido, ciphertext_leido, aad_leido)
    
    return mensaje_recuperado

def main():
    llave = RandomnessManager.generate_key()
    nombre_archivo = "secreto.txt"
    archivo_original = b"Este es un secreto super importante de la empresa."
    archivo_cifrado = encriptar(llave, archivo_original, nombre_archivo)
    archivo_descifrado = desencriptar(llave, archivo_cifrado)
    
    print(f"Archivo original: {archivo_original}")
    print(f"Archivo cifrado: {archivo_cifrado}")
    print(f"Archivo descifrado: {archivo_descifrado}")
    
if __name__ == "__main__":
    main()