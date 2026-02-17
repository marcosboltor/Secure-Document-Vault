# Secure Document Vault

## Índice

1. [Descripción General del Sistema](#1-descripcion-general-del-sistema)
2. [Diagrama de Arquitectura](#2-diagrama-de-arquitectura)
3. [Requerimientos de Seguridad](#3-requerimientos-de-seguridad)
4. [Modelo de Amenaza](#4-modelo-de-amenaza)
5. [Supuestos de Confianza](#5-supuestos-de-confianza)
6. [Revisión de Superficie de Ataque](#6-revisión-de-superficie-de-ataque)
7. [Restricciones de Diseño Derivadas de los Requisitos](#7-restricciones-de-diseño-derivadas-de-los-requisitos)


## 1. Descripcion general del sistema
La bóveda tiene como objetivo almacenar, compartir, acceder y proteger documentos en un canal inherentemente inseguro, bajo el supuesto de que:

<div align="center">

***“Any channel by default is always considered insecure”***

</div>

Protegiendo consigo aspectos muy importantes tales como:
* Confidencialidad
* Integridad
* Autenticidad
* No repudio

#### Caracteristicas principales:
Características principales
* Generación de llaves simétricas para cada archivo.
* Cifrado de archivos mediante **AEAD (Authenticated Encryption with Associated Data)**, por ejemplo AES-GCM o ChaCha20-Poly1305.
* Cifrado híbrido (key wrapping con RSA/ECC) para proteger las claves simétricas de cada archivo mediante las llaves públicas de los destinatarios.
* Firma digital obligatoria de los documentos para garantizar la autenticidad.
* Verificación de la firma antes de descifrar el contenido.
* Gestión de claves con KDF (Argon2 / PBKDF2).
* Respaldo de las llaves.
* Mecanismo de recuperación de las llaves.
* Capacidad para compartir con múltiples usuarios.
* Formato: CLI o aplicación local.

#### Alcance de nuestra boveda
El diseño de la Secure Digital Document Vault se fundamenta en un modelo de amenaza explícito y limitado. Conforme al principio de diseño conservador, se asume un adversario fuerte en el canal y almacenamiento, pero no un compromiso total del entorno de ejecución.
Por ende los siguientes escenarios quedan fuera de nuestros alcances:

#### Compromiso Total del Sistema Operativo

El sistema no protege contra escenarios donde:

* El dispositivo del usuario está infectado con malware.
* Existe un keylogger activo.
* Un atacante tiene acceso directo al dispositivo y posee privilegios root/administrador.
* Se ejecutan ataques de canal lateral (timing, power analysis, EM leakage).

**Justificación:**

La criptografía protege datos en tránsito y en almacenamiento no confiable, pero no puede proteger contra un entorno completamente comprometido. Si un atacante puede acceder a la memoria del proceso mientras la clave privada está desbloqueada, ningún esquema criptográfico puede impedir la extracción del secreto.

#### Ingeniería Social y Compromiso Humano

El sistema no cubre:

* Phishing para obtener contraseñas.
* Ingeniería social para obtener claves privadas.
* Coerción física o legal.
* Uso de contraseñas débiles por parte del usuario.

**Justificación:**

El modelo de amenaza protege activos técnicos, pero no puede prevenir fallos humanos deliberados o manipulaciones psicológicas. Esto se alinea con el modelo sistémico donde las personas son un borde vulnerable del sistema.

#### Recuperación de Contraseña sin Material de Respaldo

El sistema no incluye:

* Mecanismos de recuperación centralizada.
* Backdoors criptográficos.
* Recuperación por terceros.

**Justificación:**

Bajo el principio de Kerckhoffs, la seguridad depende únicamente de las claves. Permitir recuperación sin material de respaldo introduciría debilidades estructurales. Si el usuario pierde su contraseña y no dispone de backup seguro, la información se considera irrecuperable.

#### Infraestructura PKI Completa

El sistema no implementa:

* Autoridades Certificadoras (CA).
* Revocación automática (CRL/OCSP).
* Infraestructura empresarial de confianza.
* Gestión de identidades distribuida.

**Justificación:**

El diseño asume que las claves públicas se obtienen por un canal confiable externo. El establecimiento de una PKI completa pertenece a una arquitectura organizacional más amplia y excede el alcance de una bóveda criptográfica local.

#### Seguridad Post-Cuántica

El sistema no garantiza resistencia frente a:

* Adversarios con computación cuántica a gran escala.

**Justificación:**

El diseño adopta un nivel de seguridad clásico de ≥128 bits. La migración a esquemas post-cuánticos requeriría primitivas adicionales no consideradas en este diseño base.

## 2. Diagrama de arquitectura
![Diagrama de Arquitectura - Cripto drawio (2)](https://github.com/user-attachments/assets/04e69cc7-1d32-47c6-93be-82037ca8ee54)


## 3. Requerimientos de seguridad

Los siguientes requisitos definen formalmente las propiedades que el sistema debe garantizar bajo el modelo de amenaza especificado.

#### Confidencialidad del Contenido

**Definición**

Un adversario computacionalmente acotado que obtenga acceso completo al contenedor cifrado no debe poder:

* Recuperar el plaintext.
* Distinguir información parcial del ciphertext.
* Inferir contenido más allá de su longitud.

Esto corresponde a seguridad semántica contra chosen-plaintext attack (CPA).

**Declaración formal**

<div align="center">

***“Un atacante que obtenga el contenedor cifrado no debe poder acceder al contenido del archivo sin poseer la clave privada correcta asociada a un destinatario autorizado.”***

</div>

#### Integridad del Contenido

**Definición**

Cualquier modificación no autorizada del contenedor cifrado debe ser detectada antes de revelar el plaintext.

**Declaración formal**

<div align="center">

***“Si un solo bit del contenedor cifrado es modificado, el proceso de verificación debe fallar y el archivo no debe ser descifrado.”***

</div>

#### Autenticidad del Remitente

**Definición**

El receptor debe poder verificar criptográficamente que el archivo fue creado por el remitente declarado.

**Declaración formal**

<div align="center">

***“Un atacante no debe poder generar un contenedor válido que sea aceptado como proveniente de un remitente legítimo sin poseer su clave privada.”***

</div>

#### No Repudio

**Definición**

El remitente no debe poder negar posteriormente haber realizado alguna acción con documentos.

#### Confidencialidad de Claves Privadas

**Definición**

Un atacante que obtenga acceso al almacenamiento local no debe poder extraer claves privadas sin conocer la contraseña correcta.

**Declaración formal**

<div align="center">

***“Un atacante que obtenga el Key Store cifrado no debe poder recuperar una clave privada sin realizar un ataque de fuerza bruta computacionalmente inviable.”***

</div>

#### Protección contra Reutilización de Nonce

**Definición**

El sistema debe garantizar que nunca se reutiliza un nonce bajo la misma clave en AEAD.

**Declaración formal**

<div align="center">

***“El sistema debe emplear un generador de números aleatorios criptográficamente seguro (CSPRNG) para asegurar que cada operación de cifrado AEAD utilice un nonce único y no predecible. Si el sistema detecta o agota el espacio de nonces para una clave específica, debe invalidar la sesión de cifrado y forzar la rotación de llaves.”***

</div>

#### Protección contra Manipulación

**Definición**

Cualquier intento de modificar los metadatos o el encabezado del archivo debe ser detectado mediante la verificación del tag de autenticación (AEAD) antes de cualquier operación lógica, invalidando el proceso de apertura.

**Declaración formal**

<div align="center">

***“Toda la información no cifrada que sea crítica para el proceso (metadatos del archivo, identificadores de versión y algoritmos) debe ser vinculada criptográficamente al cifrado mediante el uso de Datos Asociados (AAD) dentro del esquema AEAD. Cualquier modificación de un solo bit en los metadatos o en el ciphertext resultará en un fallo de autenticación, provocando que la aplicación aborte el proceso de apertura sin realizar intentos de descifrado.”***

</div>


## 4. Modelo de amenaza

#### Assets - What must be protected:
* **Contenido del archivo:** Datos en texto plano del documento.
* **Metadatos:** Datos asociados del archivo como el nombre original, el algoritmo de cifrado empleado, IDs o nombres de destinatarios, manteniendo la integridad de cada uno de ellos.
* **Llaves privadas:** Elementos más críticos, almacenados en el Encrypted Key Store.
* **Contraseñas maestras:** Clave crítica, pues es la única llave capaz de desbloquear el Key Store local, si un atacante la llega a conseguir la seguridad de las llaves privadas es vulnerada en su totalidad.
* **Validez de la firma:** Funciona como una garantía de autenticidad, además de integridad de que el archivo no haya sido alterado desde el momento en que se creó.
* **Unicidad del nonce:** La reutilización destruiría la seguridad del algoritmo AES-GCM.

#### Adversaries - Who are you defending against?:
* **Atacante externo o administrador de nube:** Empleado que tiene malas intenciones y acceso al servidor donde se almacena el vault.
  * *Lo que puede hacer:* Descargar copias de los contenedores .vault almacenados, interceptar archivos y borrar archivos guardados.
  * *Lo que no puede hacer:* Acceder al contenido de los archivos, ni poder descifrar la llave de sesión sin poseer llaves privadas de destinatarios.
* **Man-in-the-Middle:**
  * *Lo que puede hacer:* Es capaz de interceptar el contenido cifrado, así como alterar bits aleatoriamente o intentar descifrar el contenido del archivo.
  * *Lo que no puede hacer:* Modificar el archivo o metadatos sin que el sistema lo detecte de forma inmediata.
* **Destinatario Malicioso:** Un compañero de clase o trabajo al que se le compartió el archivo legítimamente.
  * *Lo qué puede hacer:* Descifrar y leer el archivo original (porque fue autorizado en el cifrado híbrido).
  * *Lo qué no puede hacer:* Alterar el contenido del archivo y volver a empaquetarlo haciendo que parezca que tú hiciste esa modificación (no tiene acceso tu llave privada para generar una firma digital válida).
* **Atacantes con acceso físico temporal:** Atacante que roba el equipo del usuario o accede de forma temporal mientras el usuario no está presente.
  * *Lo que puede hacer:* Acceder y copiar el archivo encrypted key store a una memoria o servicio de nube.
  * *Lo que no puede hacer:* Acceder o extraer a las llaves privadas ni usarlas, puesto que se encontrarán protegidas. 
Perfecto — aquí tienes tu contenido reestructurado exactamente con ese formato:

## 5. Supuestos de confianza

#### Assumptions - What must hold true:

* **Confianza en los algoritmos (Principio de Kerckhoffs):**

  * Los algoritmos son públicos y auditables.
  * La seguridad depende únicamente del secreto de las claves.
  * No se asume *security by obscurity*.

* **Adversario computacionalmente acotado:**

  * El atacante puede acceder al ciphertext, modificar almacenamiento y ejecutar ataques CPA.
  * Tiene poder computacional polinomial.
  * No puede ejecutar ataques con complejidad ≥ 2¹²⁸ ni romper primitivas criptográficas modernas correctamente implementadas.

* **Entorno de ejecución parcialmente confiable:**

  * El sistema operativo no está completamente comprometido.
  * No existen keyloggers activos.
  * No hay extracción directa de memoria protegida.
  * Si el endpoint está comprometido totalmente, la seguridad criptográfica deja de ser aplicable.

* **Fuente de aleatoriedad segura:**

  * Existencia de un CSPRNG seguro.
  * Entropía suficiente.
  * No reutilización de nonces.
  * La unicidad del nonce es crítica para AES-GCM.

* **Comportamiento responsable del usuario:**

  * El usuario elige una contraseña razonablemente fuerte.
  * No la comparte.
  * No la reutiliza trivialmente.
  * El sistema mitiga fuerza bruta mediante KDF, pero no puede compensar contraseñas extremadamente débiles.

* **Autenticidad externa de claves públicas:**

  * Las claves públicas fueron obtenidas mediante un canal confiable.
  * No fueron sustituidas por un atacante.
  * No se implementa PKI completa ni verificación automática de revocación.

* **Almacenamiento hostil:**

  * El almacenamiento puede ser observado, modificado o reemplazado.
  * El diseño criptográfico debe resistir este entorno no confiable.

* **Separación estricta entre claves y datos:**

  * Las claves privadas están cifradas en reposo.
  * No se reutilizan claves de sesión.
  * No existe mezcla de dominios de claves.
  * Se sigue la definición formal de esquemas SKES.


## 6. Revisión de superficie de ataque

#### Entry Points - Where attacks may occur:


* **File Input:**

  * *What could go wrong:* Procesamiento de archivos extremadamente grandes para agotar memoria o uso de rutas no autorizadas del sistema.
  * *Security property at risk:* Disponibilidad y confidencialidad local.


* **Metadata Parsing:**

  * *What could go wrong:* Modificación del campo de algoritmo de cifrado para forzar un downgrade si los metadatos no están autenticados bajo AEAD.
  * *Security property at risk:* Integridad y confidencialidad.


* **Key Import / Export:**

  * *What could go wrong:* Sustitución de llave pública durante importación o exportación insegura de llave privada.
  * *Security property at risk:* Confidencialidad (filtración de llave privada) y autenticidad (confianza en llave falsa).


* **Password Entry (Contraseña maestra):**

  * *What could go wrong:* Uso de contraseñas de baja entropía o configuración insuficiente del costo del KDF.
  * *Security property at risk:* Confidencialidad de las llaves privadas.


* **Sharing Workflow:**

  * *What could go wrong:* Error lógico en Key Wrapping, cifrado con llave equivocada o exposición accidental en estructura JSON.
  * *Security property at risk:* Confidencialidad de la llave de sesión en tránsito.


* **Signature Verification:**

  * *What could go wrong:* Descifrar antes de verificar la firma digital.
  * *Security property at risk:* Autenticidad de origen e integridad.


* **CLI Arguments:**

  * *What could go wrong:* Pasar la contraseña como argumento en la terminal y que quede almacenada en historial en texto plano.
  * *Security property at risk:* Confidencialidad de la contraseña maestra.

## 7. Restricciones de diseño derivadas de los requisitos
* Confidencialidad del Contenido
   - Uso obligatorio de AEAD.
   - Clave simétrica única por archivo.
   - Nivel de seguridad mínimo: 128 bits.
   - Uso exclusivo de CSPRNG para generación de claves y nonces.

* Integridad
   - Uso de AEAD (tag de autenticación).
   - Rechazo inmediato ante fallo de verificación.

* Autenticidad
   - Firma digital obligatoria.
   - Verificación antes del descifrado.
   - Asociación explícita clave pública ↔ identidad.

* No Repudio
   - Uso de firmas digitales no reutilizables.
   - Asociación persistente entre clave pública y usuario.
   - Verificación determinística.

* Confidencialidad de Claves Privadas
   - Cifrar las llaves utilizando KDF resistente a fuerza bruta (Argon2 / PBKDF2).
   - Parámetros que garanticen alto costo computacional.
   - Nunca almacenar claves en texto plano.

* Protección contra Reutilización de Nonce
   - Nonce único por operación.
   - Generación mediante CSPRNG.
   - Prohibición de contadores manuales inseguros.
   - Prohibición de contadores manuales inseguros.
