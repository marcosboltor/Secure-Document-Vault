# Key Management Design (D6)

# KDF selection and parameters
Para la derivación de la llave a partir de la contraseña del usuario, el sistema utiliza **PBKDF2HMAC** (Password-Based Key Derivation Function 2).
- **Función Hash:** SHA-256.
- **Iteraciones:** 600,000. Este valor se alinea con las recomendaciones actuales de OWASP (Open Web Application Security Project) para equilibrar la seguridad contra ataques de fuerza bruta (ralentizando las GPUs del atacante) y la usabilidad del sistema (no alentarse debido a procesamiento).
- **Salt:** 16 bytes (128 bits) generados de forma criptográficamente segura mediante `os.urandom()`.
- **Salida:** Llave simétrica de 32 bytes (256 bits) que actúa como Key Encryption Key (KEK).

### Key Storage Format
Las llaves privadas **nunca** se almacenan en texto plano. Se cifran de forma autenticada empleando el algoritmo **ChaCha20Poly1305** y se estructuran en un formato JSON (`keystore`) para garantizar su portabilidad. 

Estructura del Keystore:
```json
{
  "metadata": {
    "user_id": "<string>",
    "description": "Encrypted Private Key"
  },
  "kdf_parameters": {
    "kdf_algorithm": "PBKDF2-HMAC-SHA256",
    "iterations": 600000,
    "salt": "<base64_encoded_salt>"
  },
  "nonce": "<base64_encoded_12_byte_nonce>",
  "encrypted_key": "<base64_encoded_ciphertext_and_mac_tag>"
}
```

# Backup strategy
El sistema contempla dos opciones de respaldo para garantizar la disponibilidad:

1. Keystore Export (Backup): El usuario puede exportar su archivo JSON cifrado a un medio físico (como una memoria USB) o un almacenamiento externo. Lo cual protege ante la pérdida de la base de datos central o fallos catastróficos del servidor.

1. Llave (frase) de Recuperación (Recovery): Durante la creación de la cuenta de un usuario, se genera una frase mnemónica (por ejemplo 12 palabras). Esta frase cifra una copia secundaria de la llave privada. Si el usuario olvida su contraseña principal, puede usar esta frase offline para recuperar su identidad criptográfica y generar un nuevo Keystore.

# Key Lifecycle Definition (Ciclo de Vida de las Llaves PLANTEADO)
**1. Generación y Uso (Key Generation & Usage)**
- **Generación:** Las llaves (`X25519` para intercambio y `Ed25519` para firma) se generan en el dispositivo del usuario utilizando un generador de números pseudoaleatorios criptográficamente seguro (CSPRNG).
- **Uso:** Para poder emplear las llaves (firmar o descifrar), el usuario debe ingresar su contraseña. La llave privada se descifra temporalmente y se mantiene SOLO en la memoria RAM, siendo destruida por el recolector de basura en cuanto la función u operación finaliza. 

**2. Expiración de Llaves (Key Expiration)**
Para este punto, se plantea que el sistema implemente una política de caducidad.
- **Mecanismo:** El archivo `keystore.json` incluye un campo de metadatos `expires_at` (con validez de 1 a 2 años desde su creación).
- **Comportamiento:** En el momento en el que el cliente detecta que la fecha actual ha superado el `expires_at`, la cuenta del usuario entra en "Modo Solo Lectura". En el cual, el usuario sigue siendo capaz de descifrar sus documentos históricos, pero el sistema bloquea la firma de nuevos archivos o la recepción de documentos compartidos hasta que el usuario realice la rotación de sus llaves.

**3. Rotación de Llaves (Key Rotation)**
La rotación permite renovar la identidad criptográfica sin perder acceso a los archivos cifrados del pasado.
- **Inicializador:** Este proceso puede ser iniciado de forma manual por el usuario de forma preventiva o forzada por el sistema tras alcanzar la fecha de expiración.
- **Proceso Detallado:** 
  1. El usuario desbloquea su llave actual con su contraseña.
  2. El cliente genera un nuevo par de llaves asimétricas.
  3. **Re-wrapping:** El cliente recupera las llaves simétricas (`file_keys`) de todos sus documentos, las descifra con su llave privada vieja, y las vuelve a cifrar (wrap) con su nueva llave pública.
  4. Se genera un nuevo Keystore y una nueva frase o llave de recuperación.
  5. La llave privada anterior se destruye criptográficamentes.

**4. Respuesta ante Compromiso (Key Compromise Response)**
Si el usuario se entera que su dispositivo fue robado o su contraseña expuesta, el sistema provee un mecanismo de contención.
- **Proceso de Revocación de identidad:** El usuario debe iniciar sesión desde un dispositivo seguro mediante su frase o llave de recuperación de 12 palabras. Al activar la alerta, el cliente notifica al servidor.
- **Acción del Backend:** La base de datos actualiza el estado de la llave pública comprometida a `REVOKED` (Revocada). 
- **Aislamiento:** Desde ese momento, el backend rechaza cualquier petición que provenga de dicha identidad para descargar archivos `.vault`, mitigando la exfiltración de datos. Además, de advertir a sus contactos del usuario que las firmas asociadas a esa llave ya no son confiables.

# Security assumptions
El modelo de amenazas de este módulo se basa en las siguientes suposiciones:

- **Entropía de la contraseña**: El usuario elige una contraseña lo suficientemente fuerte como para resistir ataques de diccionario (frases o patrones comunes).
- **Integridad del cliente**: El dispositivo donde el usuario introduce su contraseña y descifra la llave en la memoria RAM está libre de malware, keyloggers o acceso no autorizado.
- **Resguardo físico**: El usuario almacena su llave (frase) de recuperación o su archivo de backup de forma segura y fuera del alcance de terceros.

# Security Discussion
## Why encrypt private keys?
Uno de los eslabones más débiles de un sistema criptográfico es el almacenamiento de las llaves. Si la base de datos es vulnerada o un disco duro es robado, el cifrado garantiza que las llaves privadas (y todos los archivos del Vault) permanezcan confidenciales. Un atacante que obtenga el Keystore solo poseerá "ruido" incomprensible sin el secreto (contraseña) del usuario. 

## What happens if the password is weak?
Si la contraseña es débil (ej. "123456"), un atacante que robe o tenga acceso al Keystore puede realizar un ataque de fuerza bruta offline. A pesar de que las 600,000 iteraciones de PBKDF2 hacen que cada intento sea computacionalmente costoso, una contraseña con baja entropía (aleatoreidad) terminará siendo vulnerada. El sistema no puede proteger al usuario de sus propias malas prácticas de creación de contraseñas.

## System Limitations
Debido a la arquitectura de "Zero-Knowledge", el servidor es ciego, es decir, el sistema no puede ofrecer una funcionalidad tradicional de "Olvidé mi contraseña" por correo electrónico. Si un usuario olvida su contraseña y también pierde su frase de recuperación, sus documentos quedarán cifrados e inaccesibles para siempre.