from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.exceptions import InvalidTag

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