
# 🛡️ Secure Document Vault - Backend API

El backend de orquestación y almacenamiento seguro para el  **Secure Document Vault** . Este sistema actúa como el custodio de confianza baja (Zero-Knowledge) para contenedores cifrados (`.vault`), gestionando la persistencia de blobs binarios, autenticación, metadatos y validación de integridad.

Construido siguiendo estrictamente los principios de **Clean Architecture** para asegurar la máxima escalabilidad, seguridad y una clara separación de responsabilidades.

## 🏗️ Arquitectura del Sistema

El proyecto está diseñado bajo el principio de **Clean Architecture** (Arquitectura Limpia). La regla de oro aquí es la  **Regla de Dependencia** : las dependencias en el código fuente solo pueden apuntar hacia adentro. Las capas internas (Dominio) no saben nada sobre las capas externas (Bases de datos, Frameworks web).

### Estructura de Directorios

La estructura del código base (ubicada dentro de la carpeta `app/`) se distribuye de la siguiente manera:

```
vault_backend/
├── app/
│   ├── main.py                     # Punto de entrada de FastAPI
│   ├── core/                       # Configuración global y constantes
│   │   ├── config.py               # Settings (Pydantic) para el .env
│   │   ├── exceptions.py           # Excepciones globales (AppException)
│   │   └── dependencies.py         # Inyección de dependencias (Depends)
│   ├── domain/                     # Capa 1: Reglas de Negocio Empresariales
│   │   ├── entities.py             # Modelos puros (User, VaultFile)
│   │   └── repositories.py         # Interfaces/Contratos (UserRepository, FileStorage)
│   ├── application/                # Capa 2: Reglas de Negocio de la Aplicación
│   │   ├── dtos/                   # Modelos Pydantic para entrada/salida de datos
│   │   └── use_cases/              # Lógica de orquestación (Upload, Retrieve)
│   ├── infrastructure/             # Capa 3: Frameworks y Drivers
│   │   ├── database/               # Implementación de SQLAlchemy (Modelos y Sesión)
│   │   ├── storage/                # Implementación del Local File System
│   │   └── logging.py              # Configuración de Structlog
│   └── presentation/               # Capa 4: Adaptadores de Interfaz (Web)
│       ├── api/                    # Routers de FastAPI (endpoints v1)
│       └── middlewares/            # CORS, Manejo de errores HTTP
├── tests/                          # Suite de pruebas automatizadas (Pytest)
├── .env.example                    # Plantilla de variables de entorno
├── requirements.txt                # Dependencias del proyecto
└── alembic.ini                     # Configuración de migraciones SQL
```

### ¿Qué va en cada capa y por qué?

1. **Domain (`app/domain/`)** :

* **Qué contiene** : Las Entidades (modelos de datos sin dependencias de ORMs) y las Interfaces (clases abstractas que definen contratos, como `UserRepository`).
* **Por qué** : Es el núcleo del sistema. Aquí residen las reglas de negocio puras. No importa si usamos Postgres o MySQL, o si usamos FastAPI o Flask; el dominio nunca cambia por motivos de infraestructura.

1. **Application (`app/application/`)** :

* **Qué contiene** : Los Casos de Uso (ej. `UploadDocumentUseCase`) y los DTOs (Data Transfer Objects).
* **Por qué** : Orquesta el flujo de datos. Recibe llamadas de la API, solicita datos al dominio/infraestructura, aplica la lógica específica de la aplicación y devuelve resultados. Solo depende de la capa de Dominio.

1. **Infrastructure (`app/infrastructure/`)** :

* **Qué contiene** : El código que interactúa con agentes externos. Aquí viven los modelos reales de SQLAlchemy, la conexión a la base de datos y la escritura física de archivos en el disco duro.
* **Por qué** : Aísla los detalles técnicos. Si mañana decidimos cambiar el guardado local por AWS S3, **solo** se modifica esta carpeta implementando el contrato definido en la capa de Dominio, sin tocar los casos de uso.

1. **Presentation (`app/presentation/`)** :

* **Qué contiene** : Los "Routers" o Controladores de FastAPI y Middlewares.
* **Por qué** : Es el mecanismo de entrega. Su única responsabilidad es recibir peticiones HTTP, validarlas (usando Pydantic DTOs), pasarlas a la capa de Aplicación (Casos de Uso) y devolver una respuesta HTTP al cliente. No debe contener "ifs" ni bucles de lógica de negocio.

## ✨ Características Principales

* **Almacenamiento Desacoplado** : Gestión dual entre base de datos relacional (metadatos) y sistema de archivos (blobs binarios).
* **Defensa contra Tampering (Cumplimiento D4)** : Auditoría automática para detectar inconsistencias físicas o alteraciones manuales en los archivos almacenados.
* **Prevención AAD (Additional Authenticated Data)** : Validación cruzada de la firma digital (Ed25519) del contenedor `.vault` contra los metadatos SQL para prevenir escalamiento de privilegios en base de datos.
* **Seguridad por Diseño** : Manejador de errores estricto que previene fuga de información (Information Disclosure) al cliente.
* **API Documentada** : Especificación OpenAPI 3.0 completamente integrada.

## 🚀 Requisitos Previos

* Python 3.10 o superior

## ⚙️ Configuración y Despliegue

La aplicación utiliza variables de entorno administradas mediante `pydantic-settings`. Copia el archivo de ejemplo para comenzar:

```
cp .env.example .env
```

### Entorno Local

Sigue estos pasos para levantar el entorno de desarrollo en tu máquina local:

```
# 1. Ejecutar migraciones de base de datos (Alembic)
uv run alembic upgrade head

# 2. Iniciar servidor de desarrollo
uv run uvicorn app.main:app --reload
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación de la API

La API expone una documentación interactiva Swagger. Una vez que el servidor esté en ejecución, puedes acceder a:

* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

### Endpoints Principales

* `POST /api/v1/users` - Registro de personal y llaves públicas.
* `GET /api/v1/users` - Listado de personal autorizado.
* `POST /api/v1/files` - Carga atómica de contenedores `.vault` y metadatos.
* `GET /api/v1/files` - Listado de archivos accesibles (filtrado por Auth).
* `GET /api/v1/files/{id}/content` - Descarga en streaming de blobs binarios.

## 🧪 Pruebas y Calidad

El proyecto incluye una suite exhaustiva de pruebas unitarias implementadas con `pytest` que mockean las dependencias de infraestructura para garantizar validaciones de negocio rápidas y confiables.

```
# Ejecutar toda la suite de pruebas
pytest tests/ -v

# Comprobar la cobertura de código
pytest tests/ --cov=app/application
```

**Pruebas de Seguridad Destacadas:**

* `test_tampering_detection`: Valida el comportamiento de la API ante archivos corruptos en disco.
* `test_aad_metadata_inconsistency`: Verifica el bloqueo ante inyecciones maliciosas en metadatos SQL.

## 🛠️ Tecnologías

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/ "null")
* **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/ "null") + Alembic
* **Validación:** Pydantic
* **Observabilidad:** Structlog
* **Testing:** Pytest
