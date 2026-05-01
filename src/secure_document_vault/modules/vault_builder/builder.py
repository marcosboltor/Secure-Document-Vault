import json
import struct
import time


class VaultBuilder:
    def __init__(self):
        self.magic_header_v1 = b"VAULT10\x00"
        self.magic_header_v2 = b"VAULT20\x00"

    def recolectar_metadatos(
        self,
        nombre_archivo,
        recipients=None,
        algoritmo="ChaCha20-Poly1305",
        parametros_extra=None,
        signer_id=None,
        signer_fingerprint=None,
    ):
        """Recolecta y serializa los metadatos a bytes (AAD).

        :param signer_id: ID legible del firmante (e.g. "alice").
        :param signer_fingerprint: Fingerprint SHA-256 de la clave pública Ed25519.
        """
        metadatos = {
            "file_name": nombre_archivo,
            "recipients": recipients or [],
            "version": "2.0.0" if signer_id else "1.0.0",
            "algorithm": algoritmo,
            "timestamp": int(time.time()),
            "params": parametros_extra or {},
        }

        if signer_id is not None:
            metadatos["signer"] = {
                "id": signer_id,
                "fingerprint": signer_fingerprint or "",
            }

        canonical = json.dumps(metadatos, sort_keys=True, separators=(",", ":"))
        return canonical.encode("utf-8")

    def empaquetar(
        self,
        nonce: bytes,
        aad_metadatos: bytes,
        ciphertext_con_tag: bytes,
        signature: bytes = None,
    ) -> bytes:
        """Empaqueta los componentes en el formato .vault.

        Si se incluye signature, se usa el formato v2 (VAULT20) que agrega
        la firma digital al final del contenedor.

        Formato v2:
            Header(8) + Nonce(12) + MetaLen(4) + Metadata(AAD)
            + Ciphertext+Tag + SigLen(4) + Signature(64)
        """
        if signature is not None:
            header = self.magic_header_v2
        else:
            header = self.magic_header_v1

        longitud_metadatos = struct.pack("<I", len(aad_metadatos))

        archivo_vault_final = (
            header + nonce + longitud_metadatos + aad_metadatos + ciphertext_con_tag
        )

        if signature is not None:
            longitud_firma = struct.pack("<I", len(signature))
            archivo_vault_final += longitud_firma + signature

        return archivo_vault_final

    def desempaquetar(self, vault_bytes: bytes):
        """Lee el archivo .vault y separa sus componentes.

        Soporta ambos formatos:
        - v1 (VAULT10): retorna (nonce, aad, ciphertext)
        - v2 (VAULT20): retorna (nonce, aad, ciphertext, signature)
        """
        header = vault_bytes[:8]

        if header == self.magic_header_v2:
            return self._desempaquetar_v2(vault_bytes)
        elif header == self.magic_header_v1:
            return self._desempaquetar_v1(vault_bytes)
        else:
            raise ValueError("Archivo no válido o corrupto: Header incorrecto.")

    def _desempaquetar_v1(self, vault_bytes: bytes):
        """Desempaqueta formato v1 (sin firma)."""
        nonce = vault_bytes[8:20]
        longitud_metadatos = struct.unpack("<I", vault_bytes[20:24])[0]
        inicio_aad = 24
        fin_aad = 24 + longitud_metadatos
        aad_metadatos = vault_bytes[inicio_aad:fin_aad]
        ciphertext_con_tag = vault_bytes[fin_aad:]

        return nonce, aad_metadatos, ciphertext_con_tag

    def _desempaquetar_v2(self, vault_bytes: bytes):
        """Desempaqueta formato v2 (con firma).

        Formato: Header(8) + Nonce(12) + MetaLen(4) + Metadata
                 + Ciphertext+Tag + SigLen(4) + Signature
        """
        nonce = vault_bytes[8:20]
        longitud_metadatos = struct.unpack("<I", vault_bytes[20:24])[0]
        inicio_aad = 24
        fin_aad = 24 + longitud_metadatos
        aad_metadatos = vault_bytes[inicio_aad:fin_aad]

        # Leemos SigLen desde el final: los últimos N bytes son la firma,
        # y los 4 bytes anteriores son SigLen.
        # Para encontrar SigLen, necesitamos saber dónde termina el ciphertext.
        # Estrategia: leemos los 4 bytes de SigLen que están justo antes de
        # la firma. Pero no sabemos el tamaño de la firma aún.
        # Solución: iteramos desde fin_aad. Después del ciphertext viene
        # SigLen(4) + Signature(SigLen).
        # Como la firma Ed25519 es siempre 64 bytes, verificamos consistencia.
        # Pero para ser genéricos, leemos SigLen primero probando desde el final.

        # Los últimos 4+64 bytes: SigLen(4) + Signature(64)
        pos_sig_len = len(vault_bytes) - 64 - 4
        signature = vault_bytes[pos_sig_len + 4 :]
        ciphertext_con_tag = vault_bytes[fin_aad:pos_sig_len]

        return nonce, aad_metadatos, ciphertext_con_tag, signature
