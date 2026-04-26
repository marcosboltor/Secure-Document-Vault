# Documentación de Diseño: Firma Digital (D4)

## 1. Explicación del Diseño de Firma Digital

### ¿Por qué se necesitan firmas digitales?

Hasta el entregable D3, el sistema garantiza **confidencialidad** (mediante cifrado ChaCha20-Poly1305) y **control de acceso** (mediante cifrado híbrido multi-destinatario con X25519). Sin embargo, el sistema **no proporciona** una garantía criptográfica de **quién creó el archivo** ni de que el remitente sea auténtico.

Sin firmas digitales:
* Cualquier persona podría re-cifrar contenido y reclamar autoría.
* Los destinatarios no pueden confiar en el origen del archivo.
* Un atacante podría modificar metadatos o el texto cifrado y redistribuir el contenedor sin ser detectado por medios distintos al tag AEAD (el cual requiere la clave simétrica para verificarse).

Las firmas digitales completan el modelo de seguridad agregando **autenticidad de origen** y **no repudio**: el destinatario puede verificar criptográficamente que un archivo fue creado por un firmante específico, y el firmante no puede negar haberlo creado.

### Idea fundamental: Hash, Sign, Verify

El esquema de firma digital implementado sigue el flujo estándar:

1. **Hash:** Se computa un resumen criptográfico de los datos a firmar.
2. **Sign:** Se firma ese resumen utilizando la clave privada del remitente.
3. **Verify:** El destinatario verifica la firma utilizando la clave pública del remitente antes de proceder al descifrado.

### ¿Por qué es necesario el hashing antes de firmar?

Los algoritmos de firma digital operan sobre datos de tamaño fijo. Firmar directamente datos de tamaño arbitrario (como un archivo de varios megabytes) sería computacionalmente costoso e impráctico. Al aplicar una función hash primero, se obtiene un resumen de tamaño fijo que representa de forma única el contenido original. Cualquier modificación, incluso de un solo bit, en los datos originales producirá un hash completamente diferente, lo que invalida la firma.

En el caso de Ed25519, el algoritmo internamente aplica SHA-512 sobre los datos antes de realizar la operación de firma, por lo que el hashing está integrado en la primitiva criptográfica y no requiere un paso manual adicional.

---

## 2. Algoritmo Seleccionado: Ed25519

### ¿Qué es Ed25519?

Ed25519 es un esquema de firma digital basado en la curva elíptica de Edwards **Curve25519**, estandarizado en el RFC 8032. Utiliza el esquema de firma de Schnorr sobre la curva de Edwards retorcida (twisted Edwards curve), con SHA-512 como función hash interna.

### ¿Por qué Ed25519?

Se seleccionó Ed25519 sobre las alternativas (ECDSA, RSA-PSS) por las siguientes razones:

* **Consistencia con el sistema existente:** El sistema ya utiliza Curve25519 para el intercambio de claves (X25519 en D3). Ed25519 opera sobre la misma curva en su forma de Edwards, lo que mantiene coherencia criptográfica en todo el diseño.
* **Rendimiento:** Ed25519 es significativamente más rápido que RSA-PSS y ECDSA tanto en generación de firmas como en verificación. La firma se genera en microsegundos y la verificación es igualmente eficiente.
* **Firmas determinísticas:** A diferencia de ECDSA, Ed25519 no requiere un nonce aleatorio durante la firma. El nonce se deriva determinísticamente del mensaje y la clave privada. Esto elimina por completo la vulnerabilidad catastrófica de reutilización de nonce que ha comprometido implementaciones de ECDSA en la práctica (como el caso de Sony PlayStation 3 en 2010).
* **Tamaño compacto:** Las firmas Ed25519 son de exactamente 64 bytes y las claves públicas de 32 bytes, significativamente menores que RSA (256+ bytes para firmas RSA-2048).
* **Resistencia a ataques de canal lateral:** Las operaciones de Ed25519 están diseñadas para ejecutarse en tiempo constante, mitigando ataques de timing.
* **Nivel de seguridad:** Ed25519 proporciona aproximadamente 128 bits de seguridad, consistente con el nivel de seguridad del resto del sistema (ChaCha20 con clave de 256 bits, X25519).

### Especificaciones técnicas

| Propiedad | Valor |
|---|---|
| Curva | Curve25519 (forma Edwards) |
| Función hash interna | SHA-512 |
| Tamaño de clave privada | 32 bytes |
| Tamaño de clave pública | 32 bytes |
| Tamaño de firma | 64 bytes |
| Nivel de seguridad | ~128 bits |
| Estándar | RFC 8032 |
| Tipo de firma | Determinística (sin nonce aleatorio) |

---

## 3. Módulo de Firma: `DocumentSigner`

### Descripción

El módulo `DocumentSigner` encapsula todas las operaciones de firma digital en una clase con métodos estáticos, siguiendo el mismo patrón de diseño utilizado por los módulos existentes del sistema (`AEAD_Engine`, `ECCKeyWrapper`).

### Métodos implementados

| Método | Entrada | Salida | Propósito |
|---|---|---|---|
| `generate_key_pair()` | — | `(Ed25519PrivateKey, Ed25519PublicKey)` | Genera un par de claves Ed25519 |
| `get_fingerprint(public_key)` | `Ed25519PublicKey` | `str` (hex, 64 chars) | Calcula SHA-256 de la clave pública |
| `sign(private_key, data)` | `Ed25519PrivateKey`, `bytes` | `bytes` (64 bytes) | Firma datos con la clave privada |
| `verify(public_key, data, signature)` | `Ed25519PublicKey`, `bytes`, `bytes` | `True` / `InvalidSignature` | Verifica una firma digital |

### Identificación del firmante

Cada firmante se identifica mediante dos componentes:

* **`id`:** Identificador legible del usuario (e.g., `"alice"`), que permite al destinatario saber quién firmó el archivo de forma intuitiva.
* **`fingerprint`:** Hash SHA-256 de la clave pública Ed25519 del firmante, codificado como string hexadecimal de 64 caracteres.

La combinación de ambos proporciona legibilidad humana (`id`) y verificación criptográfica (`fingerprint`): antes de aceptar una firma como válida, el sistema puede comparar el fingerprint almacenado con el SHA-256 de la clave pública proporcionada, asegurando que no se ha sustituido la clave del firmante.

```
fingerprint = SHA-256( clave_publica_ed25519_raw_bytes )
```

---

## 4. Formato del Contenedor Actualizado (v2)

### Estructura lógica de los metadatos (AAD)

El bloque JSON de metadatos ahora incluye la información del firmante:

```json
{
  "file_name": "secreto.txt",
  "version": "2.0.0",
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
  "signer": {
    "id": "alice",
    "fingerprint": "<SHA-256 hex string de 64 caracteres>"
  },
  "timestamp": 1729012354,
  "params": {}
}
```

### Serialización binaria del archivo `.vault` v2

1. **Magic Header** (8 bytes): `VAULT20\x00` — Identifica que es formato v2 con soporte de firma digital.
2. **Nonce Maestro ChaCha20** (12 bytes): Usado para cifrar el archivo plano.
3. **Longitud de Metadatos** (4 bytes): Tamaño del JSON de los metadatos, codificado como entero de 32 bits en formato little-endian.
4. **Metadatos AAD** (Tamaño variable): Bloque JSON descrito arriba, inyectado como AAD en el motor AEAD.
5. **Ciphertext con el MAC Tag Poly1305** (Tamaño variable): Contenido del archivo cifrado.
6. **Longitud de Firma** (4 bytes): Tamaño de la firma digital (64 bytes para Ed25519), codificado como entero de 32 bits en formato little-endian.
7. **Firma Digital** (64 bytes): Firma Ed25519 sobre `metadatos_AAD || ciphertext_con_tag`.

### Compatibilidad con v1

El sistema mantiene compatibilidad retroactiva con contenedores v1 (`VAULT10`):
* El método `desempaquetar` detecta automáticamente la versión del contenedor mediante el magic header.
* Los contenedores v1 se procesan sin verificación de firma (mantienen el comportamiento anterior).
* Los contenedores v2 incluyen la firma digital como componente adicional del contenedor.

---

## 5. Decisiones de Seguridad

### ¿Por qué claves de firma separadas de las claves de cifrado?

Con la incorporación de firmas digitales, cada usuario del sistema posee ahora **dos pares de claves independientes**:

| Par de claves | Algoritmo | Propósito |
|---|---|---|
| X25519 | Curve25519 (Diffie-Hellman) | Intercambio de claves (cifrado/descifrado) |
| Ed25519 | Curve25519 (Edwards) | Firma y verificación digital |

El principio de **separación de dominios criptográficos** dicta que una clave no debe usarse para más de un propósito. Usar la misma clave para cifrado y firma puede introducir vulnerabilidades sutiles donde un atacante explota la interacción entre ambos protocolos. Al mantener pares de claves independientes (X25519 para cifrado, Ed25519 para firma), cada primitiva opera en su dominio aislado, eliminando la posibilidad de ataques de confusión de protocolo.

### ¿Por qué Ed25519 y no ECDSA o RSA-PSS?

Las firmas Ed25519 son **determinísticas**: no dependen de un nonce aleatorio generado en el momento de firmar. En ECDSA, si el nonce se reutiliza o es predecible, la clave privada puede ser recuperada completamente por un atacante. Este no es un riesgo teórico: el compromiso de la PlayStation 3 de Sony en 2010 fue causado exactamente por esta vulnerabilidad. Ed25519 elimina esta clase de ataque por diseño, ya que el nonce se deriva del hash del mensaje y la clave privada.

RSA-PSS, por otro lado, requiere claves significativamente más grandes (2048+ bits vs 256 bits) y operaciones más costosas computacionalmente, sin ofrecer un nivel de seguridad superior al proporcionado por Ed25519 (~128 bits en ambos casos).

---

## Referencias Bibliográficas

Bernstein, D. J., Duif, N., Lange, T., Schwabe, P., & Yang, B.-Y. (2012). *High-speed high-security signatures*. Journal of Cryptographic Engineering, 2(2), 77–89. https://doi.org/10.1007/s13389-012-0027-1

Josefsson, S., & Liusvaara, I. (2017). *Edwards-Curve Digital Signature Algorithm (EdDSA)* (RFC 8032). Internet Engineering Task Force. https://tools.ietf.org/html/rfc8032

Bernstein, D. J. (2006). *Curve25519: New Diffie-Hellman Speed Records*. Public Key Cryptography - PKC 2006, 335–349. https://doi.org/10.1007/11745853_21

Barker, E. (2020). *Recommendation for Key Management: Part 1 - General* (NIST Special Publication 800-57 Part 1 Revision 5). National Institute of Standards and Technology. https://doi.org/10.6028/nist.sp.800-57pt1r5

The Cryptography Project. (2024). *Cryptography: Python library which exposes cryptographic recipes and primitives*. https://cryptography.io/en/latest/

Nir, Y., & Langley, A. (2018). *ChaCha20 and Poly1305 for IETF Protocols* (RFC 8439). Internet Engineering Task Force. https://tools.ietf.org/html/rfc8439
