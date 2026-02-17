

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

