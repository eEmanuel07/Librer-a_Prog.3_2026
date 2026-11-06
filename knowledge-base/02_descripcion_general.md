# Descripción General

## Stack tecnológico

Versiones mínimas de la consigna (págs. 3-4) y lo que fija hoy `requirements.txt`.

| Capa | Tecnología | Mínimo (consigna) | En el repo |
|---|---|---|---|
| Lenguaje | Python | 3.12 | — |
| Framework web | FastAPI, todos los handlers `async def` | 0.111 | `fastapi[standard]>=0.111` |
| Modelos | SQLModel | 0.0.24 | `sqlmodel>=0.0.24` |
| ORM / motor | SQLAlchemy 2.0 asincrónico | 2.0 | `sqlalchemy[asyncio]>=2.0,<2.1` |
| Driver | asyncpg | 0.30 | `asyncpg>=0.30` |
| Base de datos | PostgreSQL | 16 | contenedor `libreria-db` (puerto 5433 en local) |
| Migraciones | Alembic, plantilla asincrónica | 1.13 | `alembic>=1.13` |
| Configuración | pydantic-settings | 2.0 | `pydantic-settings>=2.0` |
| Contraseñas | bcrypt | 4.0 | `bcrypt>=4.0` |
| Token | PyJWT | 2.8 | `PyJWT>=2.8` |
| Servidor | uvicorn (el de `fastapi[standard]`) | — | — |
| Contenedor (sólo TP 1-4) | Docker | 20.10 | — |

Tests del grupo: `unittest` de la biblioteca estándar (`python -m unittest discover -s tests`). **pytest no está en `requirements.txt`**.

## Arquitectura general

```
Petición HTTP
   │
Router  ── construye el Unit of Work con una dependencia, llama al servicio, traduce errores a 404/409
   │
Service ── reglas de negocio; recibe el UoW y lo abre con async with (nunca lo construye)
   │
Unit of Work ── confirma al salir del bloque, revierte ante una excepción, no cierra la sesión
   │
Repository ── consultas por entidad; flush() y nunca commit(); precarga declarada en el método
   │
Model (SQLModel) ── tablas, restricciones y relaciones
```

(págs. 1, 8-9, 12). La sesión es una por petición (`get_session`) y la comparten el UoW y las dependencias de autenticación, así cada petición usa una sola conexión del pool (pág. 12).

## Integraciones externas

| Servicio | Propósito | Tipo |
|---|---|---|
| PostgreSQL | Persistencia; garantiza unicidad, FK, CHECK y sólo agregado | asyncpg |
| VPS de la cátedra | Hospeda el contenedor del TP 1-4 y su base | `docker run` con `--env-file` |

No hay integraciones de pago ni de correo: el aviso del comprobante se simula con `asyncio.sleep(0.5)` y una línea en el registro (pág. 13).

## API REST (resumen de los endpoints de referencia, págs. 16-18)

Hay dos grupos de rutas montados en `main.py`. El **abierto** no pide sesión. El **protegido** lleva una sola vez el control del cambio obligatorio de contraseña, y todas sus rutas responden además 401 sin sesión y 403 con el cambio pendiente.

| Recurso | Abierto | Protegido |
|---|---|---|
| Salud | `GET /health/live`, `GET /health/ready` (503 si la base no responde) | — |
| Autenticación | `POST /auth/registro`, `/auth/login`, `/auth/logout`, `GET /auth/yo`, `POST /auth/cambiar-password` | — |
| Catálogo | `GET /libros` (filtros `titulo`, `genero_id`), `/libros/{id}`, `/editoriales`, `/generos` y sus `/{id}/libros`, `/autores/{id}/libros` | ADMIN: altas y PATCH de editoriales, géneros, autores y libros; `DELETE /libros/{id}` (204); `POST /libros/{id}/reponer`; `GET /libros/{id}/movimientos` |
| Personal | — | ADMIN: `POST /usuarios`, `POST/DELETE /usuarios/{id}/roles…`, `GET /eventos` |
| Clientes | — | VENDEDOR o ADMIN: alta, detalle, PATCH, perfil y ventas del cliente |
| Ventas | — | VENDEDOR o ADMIN: `POST /ventas`, `GET /ventas`; el personal o el cliente dueño: `GET /ventas/{id}`; autenticado: `GET /mis-ventas` |

Los listados devuelven el envoltorio `{items, total, page, size, pages}` (pág. 10). El detalle de una venta no lleva `requiere_rol`: la decisión de "personal o dueño" la toma el servicio (pág. 18).
