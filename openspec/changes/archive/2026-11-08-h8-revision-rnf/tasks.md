# Tasks: h8-revision-rnf

## 1. Auditoría de RNF y Correcciones Puntuales

- [x] 1.1 Auditar credenciales, `lazy="raise"` en modelos, `extra="forbid"` en esquemas, repositorios sin `commit()`, servicios sin `UnitOfWork` propio y traducción de errores (RN-15) en todo `app/`
- [x] 1.2 Corregir cualquier desvío detectado en código o especificaciones (`openspec/specs/autorizacion/spec.md` y `openspec/specs/datos-iniciales/spec.md`)

## 2. Suite Automatizada de Verificación de RNF (Strict TDD)

- [x] 2.1 Escribir y verificar en `tests/test_rnf.py` los tests de ausencia de secretos por defecto y limpieza de `alembic.ini`
- [x] 2.2 Escribir y verificar en `tests/test_rnf.py` los tests de introspección de `lazy="raise"` en todas las relaciones de los modelos SQLModel y ausencia de `.commit()` en repositorios
- [x] 2.3 Escribir y verificar en `tests/test_rnf.py` los tests de `extra="forbid"` en DTOs de entrada y respuesta 422/409 sin exposición de trazas ni errores 500 (RN-15)

## 3. Validación Integral y Cierre

- [x] 3.1 Ejecutar la suite completa de tests (`unittest discover -s tests`) y `openspec validate --all --strict` verificando 0 errores

## Workflow follow-up

- Archivar el change con `openspec archive h8-revision-rnf`.
- Actualizar `CHANGES.md` marcando `[H8]` como completado.
