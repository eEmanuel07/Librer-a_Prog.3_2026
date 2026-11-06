# Spec Delta: configuracion

## Purpose

Define cómo la aplicación carga y valida su configuración desde el entorno o `.env`, exige secretos explícitos sin valores por defecto y construye la URL de conexión asincrónica a PostgreSQL.

## ADDED Requirements

### Requirement: Secretos obligatorios sin valor por defecto
La configuración SHALL exigir explícitamente la contraseña de la base de datos (`POSTGRES_PASSWORD`, no vacía) y la clave de firma de tokens (`JWT_SECRET`, de al menos 32 caracteres) desde el entorno o `.env`, y SHALL NOT definir valores por defecto para ninguna de las dos ni inventar claves al arrancar.

#### Scenario: Falta la clave de firma JWT
- **WHEN** se intenta cargar la configuración sin definir `JWT_SECRET`
- **THEN** la carga falla con `RuntimeError` indicando `Configuración incompleta o inválida: JWT_SECRET` y la aplicación no arranca

#### Scenario: Clave corta y contraseña vacía
- **WHEN** `POSTGRES_PASSWORD` está vacía y `JWT_SECRET` tiene menos de 32 caracteres
- **THEN** la carga falla con `RuntimeError` nombrando ambas variables (`POSTGRES_PASSWORD, JWT_SECRET`) sin mostrar los valores ingresados

### Requirement: URL de base de datos calculada y escapada con driver asincrónico
La configuración SHALL construir `database_url` como un campo calculado (`@computed_field(repr=False)`) mediante `URL.create` de `sqlalchemy.engine` con `render_as_string(hide_password=False)` y el driver `postgresql+asyncpg` a partir de `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` y `POSTGRES_DB`, escapando caracteres reservados (`@`, `:`, `/`) en la contraseña y ocultando la URL en la representación textual de la configuración (`repr=False`).

#### Scenario: Contraseña con caracteres especiales
- **WHEN** `POSTGRES_PASSWORD` contiene caracteres reservados de URI como `@` y `/` (por ejemplo `a@b/c`)
- **THEN** `database_url` utiliza el esquema `postgresql+asyncpg://` y escapa la contraseña como `a%40b%2Fc`

### Requirement: Parámetros operativos de pool y seguridad configurables
La configuración SHALL permitir ajustar desde el entorno el tamaño del pool de conexiones (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`), la expiración del JWT (`JWT_EXPIRA_MINUTOS`), el atributo `Secure` de la cookie (`COOKIE_SECURE`), el costo de bcrypt (`BCRYPT_COSTO`) y el límite de concurrencia de bcrypt (`BCRYPT_CONCURRENCIA`) con validaciones de rango.

#### Scenario: Configuración válida completa
- **WHEN** el entorno o `.env` provee los secretos obligatorios y valores válidos
- **THEN** la aplicación y Alembic pueden conectarse a la base de datos y atender peticiones
