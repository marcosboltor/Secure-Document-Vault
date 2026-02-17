

### 4. Modelo de amenaza

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

---

### 5. Supuestos de confianza

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

---

### 6. Revisión de superficie de ataque

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

