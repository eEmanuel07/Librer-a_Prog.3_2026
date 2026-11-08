# Design: h8-revision-rnf

## Context

Con la totalidad de los módulos funcionales de la Fase 2 integrados en `main`, la tarea **[H8] (#44)** actúa como auditoría técnica y barrera de regresión para los Requisitos No Funcionales (RNF) listados en las páginas 20-21 de la consigna y en `knowledge-base/05_reglas_de_negocio.md` (§Excepciones globales y RN-15).

## UI Mockups

Decision: no (no UI)

## Goals / Non-Goals

**Goals:**
- Verificar exhaustivamente los 7 ejes de RNF:
  1. **Sin secretos en código ni repositorio:** `Settings` sin defaults para `postgres_password` ni `jwt_secret`, `alembic.ini` sin credenciales, `.env` excluido en `.gitignore`.
  2. **Prohibición de carga perezosa (`lazy="raise"`):** Todas las relaciones `Relationship` en los modelos de SQLModel deben declarar `sa_relationship_kwargs={"lazy": "raise"}`.
  3. **RN-15 (Errores propios y nunca 500 por entrada inválida):** Todos los DTOs de entrada con `extra="forbid"`, traducción limpia de `IntegrityError` en `UnitOfWork`, sin exponer trazas ni detalles crudos de SQLAlchemy/asyncpg.
  4. **Disciplina transaccional:** Ningún repositorio ejecuta `.commit()`, ningún servicio instancia su propio `UnitOfWork` (salvo la excepción explícita de `intento_acceso` en sesión independiente) y el `UnitOfWork` no cierra la sesión al salir.
  5. **SQL parametrizado:** Ausencia total de concatenación o interpolación de cadenas con entrada de usuario en consultas SQL.
  6. **Seguridad del token JWT:** Emisión y lectura exclusivamente mediante cookie `HttpOnly`, sin incluir el token en cuerpos JSON ni leerlo de cabeceras `Authorization`.
  7. **Validez de OpenSpec:** Dejar `openspec validate --all --strict` con 0 fallos.
- Codificar estas verificaciones en una suite automatizada `tests/test_rnf.py` mediante inspección de AST/reflexión de modelos y pruebas de contrato.

**Non-Goals:**
- No alterar la lógica de negocio ni las rutas aprobadas en las tareas previas, salvo para corregir eventuales incumplimientos de RNF.

## Decisions

### Decisión 1: Suite de tests de arquitectura y RNF (`tests/test_rnf.py`)
- En lugar de limitarse a una revisión manual estática, se implementará `tests/test_rnf.py` con `unittest` (siguiendo Strict TDD) para verificar por introspección:
  - Que todos los mappers registrados en `SQLModel.metadata` / `registry` tengan `lazy="raise"` en todas sus relaciones.
  - Que todas las subclases de `BaseRepository` carezcan de llamadas a `.commit()`.
  - Que todos los esquemas Pydantic de entrada (`*Create`, `*Update`, `*Request`) tengan `model_config["extra"] == "forbid"`.
  - Que `Settings` falle con `ValidationError` si faltan `POSTGRES_PASSWORD` o `JWT_SECRET`.
  - Que `alembic.ini` no contenga contraseñas ni URLs con credenciales reales.

### Decisión 2: Saneamiento de especificaciones OpenSpec
- Completar la sección `## Purpose` en `openspec/specs/autorizacion/spec.md` y `openspec/specs/datos-iniciales/spec.md` y ajustar la longitud del requerimiento en `datos-iniciales` para que `openspec validate --all --strict` pase al 100%.

## Risks / Trade-offs

- **[Riesgo: Falsos positivos al inspeccionar esquemas de respuesta]** → *Mitigación:* Filtrar claramente los DTOs de entrada (`Create`, `Update`, `Request`) de los DTOs de salida (`Read`, `Response`, `Pagina`) al validar `extra="forbid"`.
