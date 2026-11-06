# Design: h5-intento-acceso-sesion-propia

## UI Mockups

Decision: no (no UI)

## Context & Architecture

Implementación del repositorio `IntentoAccesoRepository` y la función de persistencia aislada `registrar_intento_acceso`.

## Technical Decisions

1. **Aislamiento en Unit of Work**:
   Para respetar la regla de que ningún repositorio confirma (`flush()` y no `commit()`), `IntentoAccesoRepository` solo opera sobre una sesión ya provista. La apertura de sesión aislada y confirmación se ubica en `registrar_intento_acceso` en `app/modules/usuarios/unit_of_work.py`.
2. **Subconsulta escalar en una sola query**:
   Se implementa con SQLAlchemy:
   ```python
   subquery_ultimo_exito = (
       select(func.max(IntentoAcceso.cuando))
       .where(
           IntentoAcceso.email == email,
           IntentoAcceso.ip == ip,
           IntentoAcceso.exito.is_(True),
       )
       .scalar_subquery()
   )
   ```
   Filtrando con `(subquery_ultimo_exito.is_(None) | (IntentoAcceso.cuando > subquery_ultimo_exito))` para evitar problemas con valores nulos cuando el usuario nunca tuvo un éxito previo.
3. **Zona horaria por defecto**:
   `cuando: datetime | None = None` resuelve internamente a `datetime.now(timezone.utc)` para garantizar timestamptz siempre válido.
