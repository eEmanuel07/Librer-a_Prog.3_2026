# Design: h1-modelos-usuarios

## UI Mockups

Decision: no (no UI)

## Context & Architecture

Implementación de las entidades de persistencia para el módulo de usuarios (`Usuario`, `AsignacionRol`, `IntentoAcceso`, `EventoSeguridad`) y extensión del modelo existente `Cliente`.

## Technical Decisions

1. **Prevención de N+1**:
   Todas las relaciones usan `sa_relationship_kwargs={"lazy": "raise"}` para forzar la precarga explícita mediante `joinedload` o `selectinload` en las consultas de repositorios.
2. **Relación 1 a 1 Cliente-Usuario**:
   Se modela con `cliente.usuario_id` nulo y con `unique=True` en la base. En SQLModel/SQLAlchemy se especifica `uselist=False` para que la navegación retorne una única instancia o `None`.
3. **Desambiguación de FKs en AsignacionRol**:
   Dado que `AsignacionRol` posee dos referencias a `Usuario` (`usuario_id` del beneficiario y `otorgada_por` de quien asignó el rol), se fija explícitamente `foreign_keys="[AsignacionRol.usuario_id]"` en la relación de navegación bidireccional.
4. **Fechas con zona horaria (UTC)**:
   Se utiliza `DateTime(timezone=True)` para todas las marcas temporales (`desde`, `vence_en`, `revocada_en`, `cuando`), garantizando compatibilidad con PostgreSQL `timestamptz`.
