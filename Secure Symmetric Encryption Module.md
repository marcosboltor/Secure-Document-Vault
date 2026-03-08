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

---

# Especificaciones técnicas para el diseño del cifrado

## Selected AEAD algorithm:

Para el motor criptográfico de la bóveda digital, se decidió emplear ChaCha20-Poly1305 como algoritmo de Cifrado Autenticado con Datos Asociados. 
La razón por la cual se escogió este algoritmo, es debido a cuestiones de rendimiento, pues aunque AES - GCM ofrece el mismo nivel de seguridad, necesita de soporte de hardware específico para funcionar de forma eficiente, mientras que ChaCha20 ofrece un rendimiento eficiente sólo mediante el uso de software. Asimismo, una de las razones por las cuales se eligió ChaCha20 - Poly1305, es debido a que es más resistente a ataques de timing (ataques que miden el tiempo que toma un sistema en procesar diferentes entradas y usan análisis estadísticos para correlacionar esta información de tiempos con posibles valores de la llave de descifrado), gracias a que sus operaciones son simples y se ejecutan en un tiempo constante, lo que reduce el riesgo de ataque. 

## Key size
El tamaño de llave implementado es de 256 bits. Esto debido a que es un estándar establecido por el RFC 8439 para  tener márgenes de seguridad, además este tamaño de llave, hace que los ataques de fuerza bruta sean mucho más difíciles para los atacantes con la tecnología y recursos actuales. También, otro punto a considerar, es que a pesar de que la computación cuántica representa una amenaza futura a los algoritmos presentes, tal como el algoritmo de Grover, el cual reduce la mitad de la fuerza efectiva de una llave simétrica, aún quedan 128 bits de seguridad para mantener la información segura. 

## Nonce strategy

La integridad y confidencialidad del esquema ChaCha20-Poly1305 dependen críticamente de la unicidad del nonce (Number Used Once). En cifradores de flujo, la reutilización de un nonce con la misma llave secreta resulta en una vulnerabilidad catastrófica conocida como two-time pad. Dicho ataque permite a un adversario aplicar una operación XOR entre dos textos cifrados resultantes para cancelar el flujo de claves (keystream), exponiendo el XOR de los textos planos subyacentes sin necesidad de comprometer la llave de 256 bits.

Para mitigar este riesgo estructural, la bóveda digital implementa una estrategia de generación de nonce basada estrictamente en aleatoriedad criptográfica, descartando el uso de contadores secuenciales o esquemas predecibles propensos a colisiones por reinicios del sistema, errores de estado o concurrencia multihilo. Específicamente, se ha configurado la generación de un nonce fresco de 96 bits (12 bytes), el estándar requerido por el RFC 843,  por cada proceso de cifrado, utilizando el Generador de Números Pseudoaleatorios Criptográficamente Seguro (CSPRNG) provisto nativamente por el hardware y sistema operativo subyacente.

Mediante el uso de fuentes de entropía extraídas de fenómenos de sistema imprevisibles e inherentes al equipo (a través del módulo secrets de Python), se asegura matemáticamente una distribución uniforme. Dada la longitud de 96 bits, el espacio posible de números es de $2^{96}$, lo que garantiza que la probabilidad de una colisión accidental o repetitiva (incluso bajo un volumen de cifrado masivo o en entornos paralelos) sea infinitesimalmente descartable, consolidando así la solidez teórica del algoritmo AEAD.

## Metadata authentication strategy
La estrategia de autenticación de metadatos se fundamenta en el uso de Datos Autenticados Adicionales (AAD) integrados de forma nativa en el esquema AEAD ChaCha20-Poly1305, donde información de contexto crítica como el nombre del archivo, el identificador de propietario único (owner), la versión del algoritmo y una marca de tiempo (timestamp) se serializa en formato JSON y se vincula criptográficamente al texto cifrado mediante el cálculo de la etiqueta de autenticación (MAC). Aunque estos metadatos residen en texto plano dentro del contenedor para permitir su lectura durante el parseo, esta arquitectura está diseñada específicamente para defender el sistema contra adversarios activos (Man-in-the-Middle) que intenten manipular el contexto del archivo; por ejemplo, si un atacante modifica el campo de propietario para evadir la restricción de dueño único, altera la versión para forzar un ataque de degradación (downgrade attack), o intenta un ataque de reemplazo (replay attack) modificando la línea temporal, la validación de la etiqueta de autenticación fallará irremediablemente, abortando el descifrado bajo el principio de fail-safely para garantizar la integridad absoluta de la bóveda.