# Design: j5-detalle-venta-dueno

## UI Mockups

Decision: no (no UI)

## Context

`GET /ventas/{id}` ya arma el detalle con `VentaRepository.obtener_con_detalle` (venta JOIN cliente, y renglones JOIN libro con `selectinload`), pero no pide sesión. `get_usuario_actual` (H6) resuelve el usuario desde la cookie y comparte la sesión con el Unit of Work. `AsignacionRolRepository.listar_roles_vigentes` (H6) devuelve los roles no revocados y sin vencer. `requiere_rol` (R2) todavía no está en `main`, y esta ruta no lo usa a propósito.

## Goals / Non-Goals

**Goals:**
- Que el personal (VENDEDOR o ADMIN, según la base) vea cualquier venta, y el cliente sólo las suyas.
- 401 sin sesión, 403 si la venta existe y no es personal ni dueño, 404 si no existe.
- Número fijo de consultas, también con un libro dado de baja.

**Non-Goals:**
- No se toca `GET /ventas` ni `/mis-ventas` (J6).
- No se ocultan las ventas ajenas detrás de un 404: la tabla de rutas pide 403 (C-06).

## Decisions

### 1. Decide el servicio, sin `requiere_rol`
- **Decisión:** el router sólo pide `get_usuario_actual`. `ver_venta` lee los roles vigentes y, si no hay VENDEDOR ni ADMIN, comprueba que la venta sea del cliente asociado al usuario.
- **Por qué:** con `requiere_rol("VENDEDOR", "ADMIN")` el dueño recibiría 403 aunque tenga permiso (recuadro de la pág. 18).

### 2. Primero la relación, después el detalle
- **Decisión:** para quien no es personal, `obtener_dueno` hace una consulta liviana (venta JOIN cliente, dos columnas). Si no existe → 404; si el `usuario_id` del cliente no es el del usuario → 403. Recién entonces se carga el detalle.
- **Por qué:** es el orden que pide la consigna, y no se cargan los renglones de una venta que no se va a devolver.
- **Alternativa descartada:** cargar el detalle y comprobar `venta.cliente.usuario_id` después. Ahorra una consulta al dueño, pero arma la respuesta antes de saber si se puede devolver.

### 3. Roles de la base, no del token
- **Decisión:** se usa `listar_roles_vigentes`, que filtra `revocada_en` y `vence_en`, en la misma sesión que el Unit of Work.
- **Por qué:** RN-04: revocar un rol tiene que cortar el acceso en la petición siguiente, sin esperar a que el token venza.

### 4. `SinPermiso` como error de dominio
- **Decisión:** nueva subclase de `ErrorDeDominio` en `app/core/errors.py`; el router la traduce a 403.
- **Por qué:** el servicio no conoce HTTP, igual que con `NoEncontrado` y `Conflicto`.

### 5. Libro dado de baja
- **Decisión:** el detalle trae el libro por su clave foránea, sin filtrar `borrado_en`.
- **Por qué:** una venta vieja tiene que seguir mostrando el título (C-13), y no hace falta otra consulta para eso.

## Risks / Trade-offs

- **[Trade-off] El dueño hace una consulta más que el personal:** sigue siendo fija (no depende de los renglones). C-15 se mide con el personal.
- **[Riesgo] Conflicto con R2 en `app/core/errors.py`:** si R2 agrega su propio error de permiso, se unifica con `SinPermiso` al mergear.
- **[Límite] 403 contra 404:** un cliente puede saber que existe una venta con ese id (403 en lugar de 404). Lo pide la tabla de rutas.
