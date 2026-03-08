# Módulo de Cifrado Seguro de Archivos

## Cifrado de archivos seguro

### Alcance

El sistema debe permitir:

- Generar llaves simétricas independientes para cada archivo.
- Cifrar el contenido de forma segura.
- Asociar metadatos al proceso de cifrado.
- Producir un contenedor cifrado que almacene toda la información necesaria para la posterior recuperación del archivo.

### Cómo implementarlo

Para cada archivo se genera una llave simétrica única utilizando un generador de números aleatorios criptográficamente seguro proporcionado por el sistema operativo. Esta llave se utiliza para cifrar el contenido del archivo.

El cifrado del contenido debe realizarse utilizando algoritmos criptográficos modernos. En este sistema se utilizarán esquemas de cifrado autenticado como:

- **AES-GCM**
- **ChaCha20-Poly1305**

Estos algoritmos permiten proteger tanto la **confidencialidad** como la **integridad** de los datos.

Durante el proceso de cifrado también se generan los **metadatos asociados al archivo**. Estos metadatos se vinculan criptográficamente al contenido cifrado para asegurar que no puedan ser modificados sin ser detectados.

El resultado final del proceso es un **contenedor cifrado**, el cual es una estructura de datos almacenada como archivo que incluye toda la información necesaria para verificar y descifrar el contenido protegido.

---

# Cifrado Autenticado

El sistema debe utilizar **AEAD (Authenticated Encryption with Associated Data)**. Este tipo de construcción criptográfica permite garantizar simultáneamente:

- **Confidencialidad del contenido**
- **Integridad de los datos**
- **Autenticidad del mensaje**

### Cómo implementarlo

La implementación puede realizarse utilizando funciones proporcionadas por **librerías criptográficas confiables**. Estas librerías ofrecen primitivas de cifrado autenticado que generan:

- El **texto cifrado**
- Un **valor de autenticación**

Este valor permite verificar la integridad de los datos durante el proceso de descifrado.

---

# Gestión de Nonces (IV)

Los algoritmos AEAD requieren el uso de un **nonce** (o **vector de inicialización**) durante el proceso de cifrado.

Este valor debe cumplir con las siguientes propiedades:

- Debe generarse de forma segura.
- Debe ser **único para cada operación de cifrado**.
- Debe almacenarse junto con el **texto cifrado** para permitir el descifrado posterior.

### Cómo implementarlo

Los **nonces** se generan utilizando una fuente de **aleatoriedad criptográficamente segura** proporcionada por el sistema operativo.

---

# Protección de Metadatos

El sistema debe definir un conjunto de **metadatos asociados a cada archivo cifrado**. Entre ellos se pueden incluir:

- Nombre del archivo *(opcional)*
- Versión del algoritmo utilizado
- Parámetros de cifrado
- Marca de tiempo de creación (*timestamp*)

Estos metadatos **no necesariamente deben cifrarse**, pero sí deben **protegerse contra modificaciones**.

### Cómo implementarlo

Para garantizar su integridad, los metadatos se incluyen como **Associated Authenticated Data (AAD)** dentro del esquema AEAD.

Esto significa que:

- Los metadatos **no se cifran directamente**
- Pero **sí se incluyen en el cálculo del valor de autenticación**

Este valor se denomina **authentication tag**.

De esta forma, **cualquier modificación en los metadatos será detectada** durante la verificación de autenticidad al momento de descifrar el archivo.

---

# Detección de Manipulación

El sistema debe ser capaz de detectar cualquier intento de manipulación del **contenedor cifrado**. Esto incluye:

- Modificaciones en el **texto cifrado**
- Alteraciones en los **metadatos**
- Cambios en los **parámetros utilizados durante el cifrado**

### Cómo implementarlo

Los algoritmos **AEAD** generan un **valor de autenticación** que se verifica durante el proceso de descifrado.

Si el **texto cifrado** o los **metadatos** han sido modificados, la verificación fallará.

En caso de que esta verificación no sea válida:

- El sistema debe **abortar el proceso de descifrado**
- Debe **reportar un error de autenticación**

Esto evita que se procese **información alterada o potencialmente maliciosa**.

Este mecanismo garantiza que **cualquier modificación en el contenido cifrado o en los metadatos sea detectada de manera segura**.