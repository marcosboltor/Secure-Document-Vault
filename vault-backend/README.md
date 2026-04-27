# Secure Document Vault - Backend API

Backend robusto construido con **FastAPI** siguiendo los principios de **Clean Architecture** y **Diseño Modular**. Esta arquitectura está diseñada para separar las reglas de negocio de los detalles técnicos, facilitando el desarrollo en equipo y garantizando la seguridad **Zero-Knowledge**.

---

## Arquitectura Jerárquica del Proyecto

A continuación se detalla la estructura completa del proyecto y la responsabilidad de cada componente:

```text
vault-backend/
├── app/
│   ├── main.py                     # Punto de entrada de la aplicación (FastAPI App)
│   ├── api/                        # Capa de Orquestación de la API
│   │   ├── router.py               # Router principal que une todos los módulos
│   │   └── middlewares/            # Filtros globales (CORS, Auth, Logging)
│   ├── core/                       # Núcleo de Configuración
│   │   ├── config.py               # Gestión de variables de entorno (Pydantic Settings)
│   │   ├── logger.py               # Configuración centralizada de logs (CDMX Timezone)
│   │   └── exceptions/             # Manejadores de errores globales de FastAPI
│   └── modules/                    # Módulos de Dominio (Contextos Delimitados)
│       ├── users/                  # Gestión de Identidades y Llaves Públicas
│       │   ├── domain/             # Capa 1: Reglas de Negocio Puras
│       │   │   ├── entities/       # Modelos de dominio (User)
│       │   │   └── repositories/   # Interfaces (Abstracciones de persistencia)
│       │   ├── application/        # Capa 2: Casos de Uso
│       │   │   └── use_cases/      # Lógica de aplicación (RegisterUser, Login)
│       │   ├── infrastructure/     # Capa 3: Implementaciones Técnicas
│       │   │   ├── repositories/   # Implementación SQLModel/PostgreSQL
│       │   │   └── datasources/    # Conexiones específicas a datos
│       │   └── presentation/       # Capa 4: Interfaz Externa
│       │       ├── api/            # Routers de FastAPI para usuarios
│       │       ├── schemas/        # DTOs de Pydantic (Entrada/Salida)
│       │       └── di/             # Inyección de dependencias local
│       ├── files/                  # Gestión de Documentos y Blobs
│       │   ├── domain/             # Entidades y Repositorios de Archivos
│       │   ├── application/        # Casos de Uso (Upload, Download, Delete)
│       │   ├── infrastructure/     # Implementación de Storage (Local/S3) y DB
│       │   └── presentation/       # Endpoints de archivos y Schemas
│       └── share/                  # Recursos Compartidos entre Módulos
│           ├── infrastructure/     # Implementaciones comunes
│           │   └── db/             # Sesión de Base de Datos y Alembic
│           └── exceptions/         # Excepciones base de la aplicación
├── pyproject.toml                  # Configuración de dependencias (uv)
└── alembic.ini                     # Configuración de la herramienta de migraciones
```

---

## Descripción de las Capas (Clean Architecture)

### 1. Capa de Dominio (`domain`)

Es el corazón de la aplicación. Contiene las **Entidades** (datos) y las **Interfaces** (contratos).

* **Independencia**: No puede importar nada de otras capas.
* **Contenido**: `entities.py`, `repositories.py`.

### 2. Capa de Aplicación (`application`)

Orquestra el flujo de datos hacia y desde las entidades de dominio.

* **Responsabilidad**: Aquí residen los **Casos de Uso**. Ejemplo: "Al registrar un usuario, verificar si el email existe y guardar su llave pública".
* **Contenido**: `use_cases/`.

### 3. Capa de Infraestructura (`infrastructure`)

Contiene las implementaciones técnicas de los repositorios definidos en el dominio.

* **Responsabilidad**: Hablar con la Base de Datos (PostgreSQL), sistemas de archivos, o APIs externas.
* **Contenido**: `repositories/`, `datasources/`.

### 4. Capa de Presentación (`presentation`)

Es la puerta de entrada para el mundo exterior (en este caso, una API REST).

* **Responsabilidad**: Validar los datos de entrada (Schemas) y devolver respuestas HTTP.
* **Contenido**: `api/` (Routers), `schemas/` (Pydantic models).

---

## Flujo de Trabajo para Desarrolladores

Para modificar o agregar una funcionalidad en este backend, sigue este orden:

1. **Definir el Modelo**: Si necesitas una tabla nueva, créala en `modules/xxx/domain/entities/`.
2. **Definir el Contrato**: Crea la interfaz en `repositories/` del dominio.
3. **Implementar**: Crea el código que habla con la DB en `infrastructure/repositories/`.
4. **Lógica**: Crea el Caso de Uso en `application/`.
5. **Exponer**: Crea el endpoint en `presentation/api/` y define sus Schemas.

---

## Comandos Rápidos

* **Instalar**: `uv sync`
* **Correr Dev**: `uv run uvicorn app.main:app --reload`
* **Migraciones**: `uv run alembic revision --autogenerate -m "nombre"` -> `uv run alembic upgrade head`
* **Calidad**: `uv run black .` && `uv run flake8 vault-backend`
