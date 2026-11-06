# Proposal: h1-modelos-usuarios

> Issue: #37 ([H1] — Modelos de usuarios y Cliente.usuario_id). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 2 (págs. 5 y 6).

## Nota sobre el orden: change retroactivo

Este change se escribió **después** de la implementación. Los modelos de usuarios ya estaban creados, verificados con tests y mergeados en `main` (PR #64) cuando se inicializó OpenSpec en el repo (PR #73). OpenSpec no existía aún en el proyecto cuando se realizó este trabajo. Este documento deja registrado qué se hizo, por qué y cómo se verificó, para mantener la trazabilidad completa del proyecto.

## Why

El parcial incorpora la gestión de usuarios, roles, seguridad y control de stock atribuido a usuarios. El Ejercicio 2 y los acuerdos iniciales de relaciones (E0) exigen modelar las entidades de acceso (`Usuario`, `AsignacionRol`, `IntentoAcceso`, `EventoSeguridad`) y conectar `Cliente` opcionalmente con un usuario con relación 1 a 1 (`uselist=False`), respetando la prevención de consultas N+1 con `lazy="raise"` en todas las relaciones.

## What Changes

- **Modelo `Usuario`** en `app/modules/usuarios/models.py`:
  - Columnas: `id`, `email` (UNIQUE), `nombre`, `password_hash`, `activo` (default True), `debe_cambiar_password` (default False).
  - Relaciones con `lazy="raise"`: `asignaciones` (hacia `AsignacionRol`), `movimientos` (hacia `MovimientoStock`) y `cliente` (hacia `Cliente`, `uselist=False`).
- **Modelo `AsignacionRol`** en `app/modules/usuarios/models.py`:
  - Columnas: `id`, `usuario_id` (FK a `usuario.id`, indexada), `rol`, `desde` (DateTime UTC), `vence_en` (opcional), `revocada_en` (opcional), `otorgada_por` (FK a `usuario.id`, indexada).
  - Restricciones: `CheckConstraint("rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')")`.
  - Índice único parcial: `uq_asignacion_rol_vigente` sobre `(usuario_id, rol) WHERE revocada_en IS NULL` (RN-03).
  - Desambiguación de FK: `Usuario.asignaciones` especifica `foreign_keys="[AsignacionRol.usuario_id]"` para evitar `AmbiguousForeignKeysError`.
- **Modelo `IntentoAcceso`** en `app/modules/usuarios/models.py`:
  - Columnas: `id`, `cuando` (DateTime UTC), `email`, `ip`, `exito` (bool).
  - Índice compuesto: `ix_intento_acceso_email_ip_cuando` sobre `(email, ip, cuando)`.
  - Tabla aislada sin claves foráneas (permite registrar intentos con emails inexistentes que sobreviven al rollback).
- **Modelo `EventoSeguridad`** en `app/modules/usuarios/models.py`:
  - Columnas: `id`, `cuando` (DateTime UTC), `actor` (texto), `accion` (texto).
- **Modificación en `Cliente`** (`app/modules/clientes/models.py`):
  - Columna `usuario_id` opcional, con índice UNIQUE y FK a `usuario.id`.
  - Relación `usuario` hacia `Usuario` con `uselist=False` y `lazy="raise"`.

## Capabilities

### New Capabilities

- `modelos-usuarios`: Definición de modelos declarativos de SQLModel/SQLAlchemy para cuentas de usuario, asignación de roles con historial y vigencia, bitácora de intentos de acceso y eventos de auditoría.

### Modified Capabilities

(ninguna previa)

## Impact

- **Modelos:** Agrega 4 tablas al esquema y modifica `Cliente` para asociarle cuenta web opcional.
- **Relaciones:** Se garantiza carga explícita sin N+1 con `lazy="raise"`.
- **Compatibilidad:** Permite la posterior autogeneración de la migración 3 (B6).
