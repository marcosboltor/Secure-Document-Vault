# Documentación de Diseño: Cifrado Híbrido Multi-Destinatario (D3)

## 1. Explicación del Diseño Híbrido

### ¿Por qué se utiliza el cifrado híbrido?
La criptografía de clave pública (asimétrica) es computacionalmente costosa y tiene límites estrictos sobre el tamaño de los datos que puede cifrar. No es factible cifrar archivos grandes directamente con curvas elípticas o RSA. El **cifrado híbrido** ofrece lo mejor de ambos mundos:
* **Eficiencia Simétrica:** Se utiliza un algoritmo rápido (ChaCha20Poly1305) para cifrar los datos voluminosos.
* **Seguridad Asimétrica:** Se utiliza X25519 para distribuir de forma segura la clave simétrica (`file_key`) a cada destinatario sin compartir secretos previamente.

### ¿Por qué sigue siendo necesario el cifrado simétrico?
Los algoritmos simétricos son mucho más rápidos que los asimétricos. Al usar una clave de archivo aleatoria (`file_key`) de 256 bits, podemos cifrar gigabytes de datos en segundos. Además, el uso de un modo **AEAD** (Cifrado Autenticado con Datos Adicionales) garantiza la integridad y autenticidad del archivo.

### ¿Por qué se requiere el cifrado de clave por destinatario?
Para permitir que múltiples destinatarios autorizados accedan al mismo archivo sin duplicar el contenido cifrado:
1. El archivo se cifra **una sola vez** con una `file_key` aleatoria.
2. Esa `file_key` se "envuelve" (cifra) por separado para cada destinatario usando sus claves públicas.
3. Cada destinatario solo necesita descifrar su “sobre” específico para recuperar la `file_key` maestra y acceder al contenido.

### Flujo del módulo

El flujo corresponde a la implementación que usa `ECCKeyWrapper`:

* Generación de clave efímera por cifrado
* ECDH con la clave pública del destinatario
* Derivación de key simétrica con HKDF
* Cifrado del `file_key` con ChaCha20Poly1305 (AEAD)
---

## 2. Decisiones de Seguridad

### Mecanismo de Identificación de Claves
Cada destinatario identifica su clave cifrada mediante un **ID único** almacenado en el contenedor:
* Cada entrada en la lista de recipientes contiene:
  * `id` → identificador del usuario (nombre, ID o fingerprint de clave)
  * `encrypted_key` → clave cifrada con su clave pública
* La herramienta de descifrado escanea la lista de destinatarios y busca la coincidencia con el usuario actual.

### Integración de Metadatos + AAD
Para prevenir ataques de manipulación (intercambio de destinatarios, eliminación de usuarios):
* La lista de recipientes y los identificadores de algoritmos se incluyen como **AAD** en la encriptación AEAD.
* Si un atacante modifica esta lista, la verificación del `tag` AEAD fallará y la descifrado se negará.

### Uso de Claves Efímeras
* Cada operación de `wrap_key` genera una **clave efímera** distinta.
* Esta efímera se usa solo para esa operación y se destruye después.
* Aunque un atacante tenga la clave privada del destinatario, solo podrá descifrar los `file_key` cifrados con esa clave efímera **a partir del momento en que obtiene la clave**; los anteriores permanecen seguros.

### Qué sucede si la clave pública es incorrecta
Si se utiliza una clave pública incorrecta durante `wrap_key`:
* El secreto compartido derivado (X25519 + HKDF) no coincide.
* ChaCha20Poly1305 no puede descifrar el `file_key` y `unwrap_key` genera una excepción `InvalidTag`.
* Esto garantiza que claves corruptas no revelen datos.

---

## 3. Multi-Recipient Support (D3)

### Requisitos Implementados
1. **Soporte para múltiples destinatarios**
   * Cada `file_key` se cifra individualmente con la clave pública de cada destinatario.
   * El contenedor almacena un arreglo de recipientes con objetos `{id, encrypted_key}`.

2. **Descifrado basado en destinatario**
   * Al abrir un archivo:
     1. Se identifica la entrada correspondiente al usuario.
     2. Se descifra la `file_key` usando la clave privada del usuario.
     3. Se usa la `file_key` para descifrar el contenido.
---
## 4. Formato del Contenedor Actualizado

El contenedor `.vault` ahora integra de forma nativa la lista de destinatarios dentro de la sección de Metadatos Autenticados (AAD). La estructura lógica se asemeja a:

```json
{
  "file_name": "secreto.txt",
  "version": "1.0.0",
  "algorithm": "ChaCha20-Poly1305",
  "recipients": [
    { 
      "id": "alice", 
      "encrypted_key": {
        "ephemeral_pub": "<hex string>",
        "nonce": "<hex string>",
        "encrypted_key": "<hex string>"
      } 
    },
    { 
      "id": "bob", 
      "encrypted_key": {
        "ephemeral_pub": "<hex string>",
        "nonce": "<hex string>",
        "encrypted_key": "<hex string>"
      } 
    }
  ],
  "timestamp": 1729012354
}
```

A nivel de serialización binaria, el archivo `.vault` queda de la siguiente manera:

1. **Magic Header** (8 bytes): Identifica que es formato `VAULT10`.
2. **Nonce Maestro ChaCha20** (12 bytes): Usado para cifrar el archivo plano.
3. **Longitud de Metadatos** (4 bytes): Tamaño del JSON de los Metadatos.
4. **Metadatos AAD** (Tamaño variable): Todo el bloque JSON descrito arriba.
   * *Consideración Crítica:* Al estar estos metadatos inyectados como **AAD (Associated Authenticated Data)** directo al motor ChaCha20, cualquier intento de remover, duplicar o cambiar un recipiente resultará en un "Invalid MAC Tag". Las modificaciones indetectables son matemáticamente inviables. 
5. **Ciphertext con el MAC Tag Poly1305** (Tamaño variable).

## Referencias Bibliográficas

Barker, E., & Dang, Q. (2020). *Recommendation for Key-Derivation Methods in Key-Establishment Schemes* (NIST Special Publication 800-56C Revision 2). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-56Cr2

Bernstein, D. J. (2006). *Curve25519: New Diffie-Hellman Speed Records*. Public Key Cryptography - PKC 2006, 335–349. https://doi.org/10.1007/11745853_21

Krawczyk, H., & Eronen, P. (2010). *HMAC-based Extract-and-Expand Key Derivation Function (HKDF)* (RFC 5869). Internet Engineering Task Force. https://tools.ietf.org/html/rfc5869

Nir, Y., & Langley, A. (2018). *ChaCha20 and Poly1305 for IETF Protocols* (RFC 8439). Internet Engineering Task Force. https://tools.ietf.org/html/rfc8439

The Cryptography Project. (2024). *Cryptography: Python library which exposes cryptographic recipes and primitives*. https://cryptography.io/en/latest/