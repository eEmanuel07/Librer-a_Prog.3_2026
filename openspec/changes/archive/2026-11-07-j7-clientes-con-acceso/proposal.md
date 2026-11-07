# Proposal: j7-clientes-con-acceso

> Issue: #60 ([J7] — Clientes protegido, con usuario_id y el envoltorio). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 3 (pág. 10), Ejercicio 5 y RN-04 (pág. 7), tabla de rutas (pág. 18), cambios del modelo (pág. 4).

## Why

El módulo clientes quedó como en el TP: cualquiera con sesión (incluido un CLIENTE) puede ver y editar fichas, la ficha no muestra si el cliente tiene acceso web, y las ventas de un cliente salen como lista con `limit`/`offset`. La consigna pide que todas sus rutas sean del personal (VENDEDOR o ADMIN), que el cliente tenga `usuario_id` y que los listados usen el envoltorio. Con R2 en `main`, además, `POST /ventas` y `GET /ventas` pueden pasar a `requiere_rol`: hoy un CLIENTE puede registrar una venta.

## What Changes

- **Router de clientes**: `requiere_rol("VENDEDOR", "ADMIN")` como dependencia de todo el router (401 sin sesión, 403 sin el rol).
- **Contrato de clientes**: `ClienteRead` agrega `usuario_id` (nulo si no tiene acceso web), sólo de lectura: el alta y el PATCH lo rechazan con 422 (`extra="forbid"`), porque lo pone el auto-registro (RN-02).
- **Ventas de un cliente**: `GET /clientes/{id}/ventas` devuelve `Pagina[VentaRead]` con `page`/`size` (B5); el repositorio usa `paginar`.
- **Ventas**: `POST /ventas` y `GET /ventas` usan `requiere_rol("VENDEDOR", "ADMIN")`; se quita el control provisorio del servicio de `GET /ventas` (J6).
- **`app/core/pagination.py`**: se borra; clientes era el último que lo importaba (pregunta abierta de B5).
- **`test/clientes.http`**: login con cookie (patrón de `seguridad.http`), casos 401/403, `usuario_id`, envoltorio y `{{x.response.body.$.id}}`.
- **Tests**: `tests/test_clientes_protegido.py` nuevo; se ajustan los de J4 y J6 al rol en el router.

## Capabilities

### New Capabilities

- `clientes`: módulo de clientes del personal, con `usuario_id` y ventas paginadas.

### Modified Capabilities

- `ventas`: registrar y listar todas las ventas exige rol de personal con `requiere_rol`.

## Impact

- **Autorización:** un CLIENTE recibe 403 en `/clientes/...` y en `POST /ventas`.
- **Contrato:** `GET /clientes/{id}/ventas` pasa de lista a envoltorio; la ficha suma `usuario_id`.
- **Archivos de otros:** `test/clientes.http` (Belén, del TP) se reescribe porque sin login todo daba 401.
