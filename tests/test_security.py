import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from encryption_module import (  # noqa: E402
    RandomnessManager,
    encriptar,
    desencriptar,
    IntegrityErrorException,
)


# ESCENARIO 1
# Cifrado y descifrado correcto
def test_encrypt_decrypt_success():
    key = RandomnessManager.generate_key()

    nombre_archivo = "archivo.txt"
    plaintext = b"Mensaje secreto de prueba"

    vault = encriptar(key, plaintext, nombre_archivo)
    recovered = desencriptar(key, vault)

    assert recovered == plaintext


# ESCENARIO 2
# Detectar modificación en el ciphertext
def test_ciphertext_tampering():
    key = RandomnessManager.generate_key()

    plaintext = b"Datos importantes"
    nombre_archivo = "doc.txt"

    vault = encriptar(key, plaintext, nombre_archivo)

    corrupted = bytearray(vault)
    corrupted[-5] ^= 1  # modificamos un byte del ciphertext

    with pytest.raises(IntegrityErrorException):
        desencriptar(key, bytes(corrupted))


# ESCENARIO 3
# Detectar modificación en metadatos (AAD)
def test_metadata_tampering():
    key = RandomnessManager.generate_key()

    plaintext = b"Archivo confidencial"
    nombre_archivo = "secreto.txt"

    vault = encriptar(key, plaintext, nombre_archivo)

    corrupted = bytearray(vault)

    # modificamos un byte dentro de los metadatos
    corrupted[29] ^= 1

    with pytest.raises(IntegrityErrorException):
        desencriptar(key, bytes(corrupted))


# ESCENARIO 4
# Intentar descifrar con llave incorrecta
def test_wrong_key():
    key_correct = RandomnessManager.generate_key()
    key_wrong = RandomnessManager.generate_key()

    plaintext = b"Contenido ultra secreto"
    nombre_archivo = "empresa.txt"

    vault = encriptar(key_correct, plaintext, nombre_archivo)

    with pytest.raises(IntegrityErrorException):
        desencriptar(key_wrong, vault)


# ESCENARIO 5
# Verificar que el nonce es diferente en cada cifrado
def test_nonce_randomness():
    key = RandomnessManager.generate_key()

    plaintext = b"Mismo mensaje"
    nombre_archivo = "file.txt"

    vault1 = encriptar(key, plaintext, nombre_archivo)
    vault2 = encriptar(key, plaintext, nombre_archivo)

    assert vault1 != vault2
