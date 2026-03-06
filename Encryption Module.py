import json, struct, time, os

class VaultBuilder:
    def __init__(self):
        # Header o "Magic Number" para identificar que es nuestro archivo .vault
        self.magic_header = b'VAULT10\x00' # 8 bytes

    def recolectar_metadatos(self, nombre_archivo, algoritmo="AES-256-GCM", parametros_extra=None):
        """
        Paso 1 y 2: Recolecta y serializa los metadatos a bytes.
        """
        metadatos = {
            "file_name": nombre_archivo,
            "version": "1.0.0",
            "algorithm": algoritmo,
            "timestamp": int(time.time()),
            "params": parametros_extra or {}
        }
        
        # Serializamos el diccionario a JSON y luego a bytes (UTF-8)
        metadatos_bytes = json.dumps(metadatos).encode('utf-8')
        return metadatos_bytes

    def empaquetar(self, nonce, aad_metadatos, ciphertext, auth_tag):
        """
        Paso 4: Empaqueta todos los componentes en un solo bloque de bytes.
        """
        # Calculamos el tamaño exacto de los metadatos (AAD) para saber dónde terminan al leer.
        # '<I' significa un entero sin signo (unsigned int) de 4 bytes en formato Little-Endian.
        longitud_metadatos = struct.pack('<I', len(aad_metadatos))

        # Concatenamos todo en el orden estricto de nuestro contenedor
        archivo_vault_final = (
            self.magic_header +
            nonce +                # Entregado por Dev 1 (o generado antes)
            longitud_metadatos +   # 4 bytes
            aad_metadatos +        # Tamaño variable
            ciphertext +           # Tamaño variable, entregado por Dev 1
            auth_tag               # 16 bytes (usualmente), entregado por Dev 1
        )
        
        return archivo_vault_final