# Proposal: r9-seguridad-http

## Why

La consigna del Parcial (págs. 21-23 y Ejercicio 5) exige el archivo `test/seguridad.http` con los casos de prueba mínimos **C-06 a C-09** para ejecutarlos con la extensión REST Client de VS Code después de correr `python seed.py`.

## What Changes

- Se crea `test/seguridad.http` parametrizado con `@host = http://localhost:8000`, utilizando `# @name` en cada login y `# @no-cookie-jar` con `Cookie: {{loginX.response.headers.Set-Cookie}}` en las peticiones subsiguientes para mantener varias sesiones abiertas en el mismo archivo:
  - **C-06 (401 contra 403 y acceso a lo propio):**
    - Petición sin sesión a ruta protegida (`POST /editoriales/`, `GET /mis-ventas`, `GET /eventos`) → `401 Unauthorized`.
    - Petición con sesión pero sin el rol requerido (`VENDEDOR` intentando `POST /editoriales/`, `POST /usuarios` o `GET /eventos`) → `403 Forbidden`.
    - Acceso a lo propio (`RN-14`): `ana@example.com` (`CLIENTE`) consulta `GET /mis-ventas` → `200 OK`, e intenta ver la venta 1 de Lucía (`GET /ventas/1`) → `403 Forbidden` (mientras que el vendedor sí la ve con `200 OK`).
  - **C-07 (Revocar un rol con la sesión abierta, RN-04):**
    - `admin@example.com` asigna temporalmente un rol o se verifica la sesión abierta de `vendedor@example.com` (o de un usuario con rol vigente), `admin@example.com` revoca el rol con `DELETE /usuarios/{id}/roles/{rol}` (`200 OK`), y en la petición siguiente con la misma cookie ya emitida el endpoint responde `403 Forbidden` y `GET /auth/yo` muestra el rol en `roles_token` pero ya no en `roles`.
  - **C-08 (Autoprotección de ADMIN y validaciones de vigencia, RN-05):**
    - `admin@example.com` intenta revocarse su propio rol `ADMIN` (`DELETE /usuarios/1/roles/ADMIN`) → `409 Conflict`.
    - `admin@example.com` revoca el rol `ADMIN` de `admin2@example.com` (`200 OK`) y cuando sólo queda un administrador vigente, cualquier intento de dejar el sistema sin administradores se rechaza con `409 Conflict`; luego le reasigna `ADMIN` a `admin2@example.com`.
    - Vencimiento inválido (`vence_en` sin zona horaria o en el pasado) → `422 Unprocessable Entity`.
    - Asignación duplicada del mismo rol vigente (`RN-03`) → `409 Conflict`.
  - **C-09 (Cambio obligatorio de contraseña y auditoría, RN-06, RN-16):**
    - `nuevo@example.com` (`debe_cambiar_password=True`) inicia sesión (`200 OK` con `"debe_cambiar_password": true`).
    - Intenta usar rutas del grupo protegido (`GET /mis-ventas`, `GET /ventas/1`) → `403 Forbidden`.
    - Puede usar las rutas abiertas (`GET /libros/`, `GET /auth/yo` → `200 OK`) y `POST /auth/cambiar-password` (`200 OK`).
    - Tras cambiar su contraseña, con la misma cookie ya puede acceder a las rutas del grupo protegido (`GET /mis-ventas`, `GET /ventas/1` → `200 OK`).
    - `admin@example.com` consulta `GET /eventos` (`200 OK` con envoltorio `Pagina`) viendo la línea inicial de `SISTEMA` y los eventos de auditoría registrados.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `autorizacion`: Documenta la cobertura ejecutable de los casos C-06 a C-09 en `test/seguridad.http`.

## Impact

- Agrega `test/seguridad.http`. No modifica código de producción en `app/`.
