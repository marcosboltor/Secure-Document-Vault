import json
import struct
import time


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
        """Lee el archivo .vault y separa sus componentes."""
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
