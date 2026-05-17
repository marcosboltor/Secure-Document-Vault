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

# Security Assumptions (Supuestos de Seguridad)
El modelo de amenazas de este módulo se basa en los siguientes supuestos:

- **Entropía de la contraseña**: El usuario elige una contraseña robusta (alta entropía) que no pueda ser adivinada mediante ataques sencillos de diccionario.
- **Integridad del cliente**: El dispositivo físico donde el usuario ejecuta el software y descifra su llave privada en la memoria RAM está libre de troyanos, keyloggers, spywares o acceso remoto no autorizado.
- **Almacenamiento del Backup**: El usuario resguarda sus archivos de respaldo (`.keystore`) y su frase de recuperación de 12 palabras de forma segura y separada del entorno de producción habitual.

# Threat Model Alignment & Security Discussion (Alineación con el Modelo de Amenazas y Discusión de Seguridad)

Para cumplir formalmente con las directrices del entregable D6, detallamos a continuación las respuestas a las interrogantes de seguridad críticas:

### 1. ¿Qué pasa si un atacante roba el Keystore? (What if an attacker steals the keystore?)
Si un atacante externo o un administrador malicioso del servidor obtiene acceso al almacenamiento y roba el archivo JSON del Keystore (o la base de datos de respaldo), **no podrá descifrar ni extraer las llaves privadas del usuario** de forma directa. 
- **Razón técnica:** Las llaves privadas están cifradas con **ChaCha20Poly1305** usando una llave KEK de 256 bits derivada de la contraseña a través de **PBKDF2-HMAC-SHA256** con **600,000 iteraciones**.
- **Seguridad:** A menos que el atacante posea o logre adivinar la contraseña maestra del usuario, el Keystore robado es indistinguible de ruido aleatorio criptográfico. Además, al usar cifrado autenticado (AEAD), cualquier intento de modificar los bits del Keystore robado para vulnerar el sistema será detectado inmediatamente al verificar la firma de autenticación (Tag), provocando que el descifrado aborte de inmediato.

### 2. ¿Qué pasa si la contraseña es débil? (What if a password is weak?)
Si la contraseña del usuario es débil (baja entropía, ej. "123456" o "password"), la seguridad del sistema se ve **gravemente comprometida** si el atacante logra exfiltrar el Keystore.
- **Vulnerabilidad:** Aunque las 600,000 iteraciones de PBKDF2 ralentizan drásticamente los intentos de adivinación (haciendo que los ataques con hardware masivo como GPUs sean extremadamente costosos), una contraseña de diccionario o muy corta terminará siendo revelada mediante un ataque de fuerza bruta offline.
- **Mitigación:** El sistema ralentiza el ataque, pero no puede sustituir la falta de entropía del secreto elegido por el usuario. Es responsabilidad del usuario elegir contraseñas de alta calidad.

### 3. ¿Qué pasa si el dispositivo del usuario está comprometido? (What if a device is compromised?)
Si el dispositivo final del usuario está infectado con malware, tiene un keylogger activo, o un atacante tiene control total (root/administrador), **todas las garantías de seguridad criptográfica se pierden por completo**.
- **Impacto:** El atacante podría interceptar la contraseña maestra cuando el usuario la escribe, extraer la clave privada en texto plano directamente desde la memoria RAM mientras está desbloqueada temporalmente, o manipular la lógica de la aplicación para exfiltrar las llaves de los archivos antes de que sean destruidas. 
- **Postura del sistema:** El sistema se diseña asumiendo que el dispositivo cliente mantiene su integridad operacional (Supuesto de Cliente Confiable). La criptografía protege los datos "en tránsito" y "en reposo hostil", pero no puede defenderse de un entorno de ejecución local corrupto.

---

## Preguntas de Discusión Requeridas (D6 Rubric)

### ¿Por qué cifrar las llaves privadas? (Why encrypt private keys?)
La llave privada es la raíz de toda la identidad, firma y capacidad de descifrado del usuario en la bóveda. Si las llaves privadas se almacenaran en texto plano en el disco local o base de datos, cualquier compromiso del sistema operativo, robo físico del dispositivo o exfiltración de archivos revelaría inmediatamente el acceso total a todos los documentos históricos y futuros del usuario. Cifrar la llave privada bajo una contraseña derivada asegura que el material criptográfico más crítico permanezca protegido incluso si el medio de almacenamiento es totalmente hostil.

### ¿Qué protege y qué NO protege nuestro sistema? (Protections vs. Non-Protections)

#### Lo que SÍ protege:
- **Compromiso del Servidor (Server Compromise):** Un atacante que controle la base de datos central o los servidores en la nube no puede descifrar los archivos ni las llaves privadas de los usuarios.
- **Ataques en el Canal de Comunicación (Man-in-the-Middle):** El tráfico interceptado solo contiene paquetes cifrados y firmas digitales verificables.
- **Alteraciones del Contenedor (Tampering):** Gracias al uso de AEAD (ChaCha20Poly1305), cualquier modificación no autorizada de los datos o metadatos del Keystore o los archivos `.vault` es detectada y rechazada.
- **Ataques offline de fuerza bruta tradicionales:** Mediante el alto número de iteraciones (600k) de PBKDF2, se disuade la fuerza bruta rápida para contraseñas de entropía media/alta.

#### Lo que NO protege (Supuestos excluidos):
- **Malware y Compromiso de Dispositivo Local:** Keyloggers, extractores de memoria RAM o rootkits que comprometan el cliente.
- **Entropía Nula en Contraseñas:** Contraseñas extremadamente cortas o comunes (susceptibles a ataques offline de fuerza bruta).
- **Pérdida de Credenciales de Recuperación:** Si el usuario olvida su contraseña maestra y pierde su frase de recuperación, la información cifrada es permanentemente inaccesible (arquitectura Zero-Knowledge).
- **Ingeniería Social y Coerción:** Phishing o coerción física/legal al usuario para revelar la clave o contraseña.

### Limitaciones del Sistema (System Limitations)
La principal limitación radica en el modelo de **Cero Conocimiento (Zero-Knowledge)**. Debido a que el servidor no almacena contraseñas ni llaves en texto plano, no existe un flujo centralizado de "Restablecer Contraseña por Email". Si un usuario pierde tanto su contraseña como su frase semilla, no hay forma matemática ni técnica de recuperar su cuenta, resultando en la pérdida irreversible de sus datos.