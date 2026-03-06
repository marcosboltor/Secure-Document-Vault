import json, struct, time, os
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.exceptions import InvalidTag

#Dev 1 Sebastian
class IntegrityErrorException(Exception):
    pass

class AEAD_Engine:
    def __init__(self, key: bytes):
        '''Initializes the cryptographic motor.

        :param key: The 256 bit simetric key generated
        '''
        self.chacha20 = ChaCha20Poly1305(key)

    def encrypt(self, nonce: bytes, plaintext: bytes, aad: bytes) -> bytes:
        '''
        Encrypts the data and links it with the metadata

        :param nonce: A single-use value in bytes. 
        :param plaintext: The content of the original file in bytes. 
        :param aad: The associated metadata in bytes. 
        :return: The ciphertext in bytes (as it includes the authentication label).
        '''
        ciphertext = self.chacha20.encrypt(nonce, plaintext, aad)
        return ciphertext
        

    def decrypt(self, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
        """
        Decrypts the data and verifies its integrity/authenticity.
        
        :param nonce: The same nonce used for encrypting.
        :param ciphertext: Ciphertext in bytes.
        :param aad: The same metadata used for encrypting. 
        :return: The original text plain in bytes.
        """
        try:
            plaintext = self.chacha20.decrypt(nonce, ciphertext, aad)
            return plaintext
        except InvalidTag:
            message = "SECURITY ALERT: The file or metadata has been modified or the key is incorrect"
            print(f">>>> ERROR: {message} >>>>")
            raise IntegrityErrorException(message)

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

def main():
    llave_secreta = os.urandom(32) # Llave de 256 bits para ChaCha20
    mensaje_original = b"Este es un secreto super importante de la empresa."
    nombre_archivo = "secreto.txt"
    
    dev1_engine = AEAD_Engine(llave_secreta)
    dev3_builder = VaultBuilder()

    print("=== FASE 1: CIFRADO Y EMPAQUETADO ===")
    aad_bytes = dev3_builder.recolectar_metadatos(nombre_archivo)
    nonce_generado = os.urandom(12)
    ciphertext = dev1_engine.encrypt(nonce_generado, mensaje_original, aad_bytes)
    archivo_vault = dev3_builder.empaquetar(nonce_generado, aad_bytes, ciphertext)
    print(f"[+] Archivo .vault empaquetado. Tamaño total: {len(archivo_vault)} bytes.\n")
    
    print("=== FASE 2: DESEMPAQUETADO Y DESCIFRADO ===")    
    nonce_leido, aad_leido, ciphertext_leido = dev3_builder.desempaquetar(archivo_vault)
    print(f"[*] Metadatos recuperados: {aad_leido.decode('utf-8')}")
    
    try:
        mensaje_recuperado = dev1_engine.decrypt(nonce_leido, ciphertext_leido, aad_leido)
        print(f"[+] ¡Éxito! Mensaje recuperado: {mensaje_recuperado.decode('utf-8')}")
    except IntegrityErrorException as e:
        print(f"[-] Falló el descifrado: {e}")

if __name__ == "__main__":
    main()