# Proposal: j8-ventas-http-c15

> Issue: #61 ([J8] — test/ventas.http y evidencia de C-15). Consigna: `Parcial_Cap1a6_Consigna.pdf`, casos C-10, C-11, C-12 y C-15 (págs. 22-23), entrega (pág. 24).

## Why

`test/ventas.http` era el del TP: sin login (hoy todo da 401), con `limit`/`offset` y sin los casos nuevos del parcial. La entrega pide los `.http` con los casos y, en `evidencia/`, el fragmento de consola de C-15: el detalle de una venta con 2 renglones y el de otra con 4 hacen la misma cantidad de consultas.

## What Changes

- **`test/ventas.http`** reescrito sobre los datos de `seed.py`, con login por cookie (patrón de `seguridad.http`) y `{{x.response.body.$.id}}`:
  - acceso: 401 sin sesión y 403 para un CLIENTE al registrar;
  - C-10 (201, total 72000, stock y movimiento «Venta», aviso en la consola);
  - C-11 (409 nombrando a Bestiario; Rayuela y los movimientos no cambian);
  - C-12 (cliente inexistente, libro inexistente y libro dado de baja: 409 sin escrituras);
  - contrato del TP (422 y 405), detalle (J5), listados con el envoltorio (J6);
  - C-15: una venta de 4 renglones y los dos detalles para comparar con `SQL_ECHO=true`.
- **`evidencia/C-15_consultas_detalle.txt`**: la salida de la consola de los dos `GET /ventas/{id}`: 4 SELECT en cada uno.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `ventas`: agrega el requisito de los casos manuales y la evidencia de C-15.

## Impact

- Sin cambios de código: sólo `test/ventas.http`, `evidencia/` y OpenSpec.
- El archivo supone una base recién cargada con `python seed.py` (ids y stock de la consigna).
