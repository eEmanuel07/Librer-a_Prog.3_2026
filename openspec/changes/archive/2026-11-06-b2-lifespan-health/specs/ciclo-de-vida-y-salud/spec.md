# Spec Delta: ciclo-de-vida-y-salud

## Purpose

Define cómo la aplicación inicializa y libera los recursos compartidos durante su ciclo de vida (motor de base de datos con pool configurable, fábrica de sesiones y hash ficticio en el estado de la aplicación), cómo entrega una sesión por petición y cómo expone los endpoints de diagnóstico de vida (`/health/live`) y de disponibilidad de la base de datos (`/health/ready`).

## ADDED Requirements

### Requirement: Recursos compartidos creados en el ciclo de vida y liberados al apagar
La aplicación SHALL crear el motor de base de datos, la fábrica de sesiones y el hash ficticio de contraseñas al iniciar su ciclo de vida (`lifespan`) y guardarlos en el estado de la aplicación (`app.state`), y SHALL NOT crearlos al importar módulos. Al finalizar el ciclo de vida, la aplicación SHALL cerrar el pool de conexiones del motor (`dispose()`).

#### Scenario: Importación sin abrir conexiones ni leer variables de entorno
- **WHEN** se importa el módulo de base de datos o la aplicación sin iniciar el ciclo de vida
- **THEN** no se crea ningún motor ni se abren conexiones a PostgreSQL

#### Scenario: Arranque y apagado del ciclo de vida
- **WHEN** la aplicación inicia su ciclo de vida y luego se apaga
- **THEN** durante la ejecución `app.state` expone la configuración, el motor, la fábrica de sesiones y el hash ficticio, y al apagarse el motor libera su pool con `dispose()`

### Requirement: Pool de conexiones configurado desde el entorno
El motor de base de datos SHALL configurarse con el tamaño de pool (`db_pool_size`) y el máximo de conexiones adicionales (`db_max_overflow`) definidos en la configuración de la aplicación.

#### Scenario: Valores personalizados del pool
- **WHEN** la configuración define valores específicos para `db_pool_size` y `db_max_overflow`
- **THEN** el motor se construye con ese tamaño de pool y ese límite de conexiones adicionales

### Requirement: Sesión por petición sin expiración tras confirmar
Cada petición que requiera acceso a la base de datos SHALL recibir una sesión asincrónica creada desde la fábrica de `app.state` con `expire_on_commit=False`, y la sesión SHALL cerrarse automáticamente al finalizar la petición.

#### Scenario: Objetos usables después de confirmar sin recarga implícita
- **WHEN** una sesión creada por la fábrica confirma una transacción
- **THEN** sus instancias cargadas permanecen con sus atributos en memoria (`expire_on_commit=False`) sin disparar consultas perezosas

### Requirement: Chequeo de vida independiente de la base de datos
El endpoint `GET /health/live` SHALL responder `200 OK` con `{"estado": "vivo"}` sin abrir sesión ni ejecutar consultas contra la base de datos.

#### Scenario: Proceso activo con la base de datos disponible
- **WHEN** un cliente envía `GET /health/live` con la aplicación en marcha
- **THEN** la API responde `200` con `{"estado": "vivo"}` sin consultar la base

#### Scenario: Proceso activo con la base de datos caída
- **WHEN** la base de datos no está disponible y un cliente envía `GET /health/live`
- **THEN** la API igualmente responde `200` con `{"estado": "vivo"}`

### Requirement: Chequeo de disponibilidad verificando la base de datos
El endpoint `GET /health/ready` SHALL verificar la conectividad con la base de datos ejecutando `SELECT 1`. Si la consulta responde sin error, SHALL devolver `200 OK` con `{"estado": "listo", "base": "ok"}`. Si la base de datos no responde o lanza un error de conexión o de SQLAlchemy, SHALL responder `503 Service Unavailable` con un mensaje propio del dominio y SHALL NOT incluir texto interno del motor ni trazas en la respuesta (RN-15).

#### Scenario: Base de datos disponible
- **WHEN** la base de datos responde a `SELECT 1` y un cliente envía `GET /health/ready`
- **THEN** la API responde `200` con `{"estado": "listo", "base": "ok"}`

#### Scenario: Base de datos caída o inalcanzable
- **WHEN** la consulta a la base de datos falla por un error de SQLAlchemy o de red (`OSError`) al pedir `GET /health/ready`
- **THEN** la API responde `503` con `{"detail": "La base de datos no está disponible"}` y sin exponer detalles técnicos ni trazas de la base
