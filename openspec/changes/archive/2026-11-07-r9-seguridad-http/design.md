# Design: r9-seguridad-http

## Context

La issue #53 (`[R9]`) pide `test/seguridad.http` con los casos C-06 a C-09 ejecutables con REST Client en VS Code después de `python seed.py`. Como REST Client comparte por defecto un único cookie jar global por dominio, iniciar sesión con un segundo usuario pisaría la cookie del primero.

## Goals / Non-Goals

**Goals:**
- Mantener múltiples sesiones simultáneas en `test/seguridad.http` (`loginAdmin`, `loginVendedor`, `loginAna`, `loginNuevo`) nombrando cada login con `# @name` y colocando `# @no-cookie-jar` + `Cookie: {{loginX.response.headers.Set-Cookie}}` en cada petición autenticada.
- Dejar que el archivo se pueda correr de principio a fin después de `python seed.py`, restaurando el rol `VENDEDOR` de `vendedor@example.com` luego de demostrar la revocación en caliente de C-07 si se necesita en pasos posteriores.

**Non-Goals:**
- No modifica endpoints ni modelos.

## Decisions

### 1. Múltiples sesiones simultáneas con `# @no-cookie-jar`
- **Decisión:** Cada `POST /auth/login` lleva `# @name login...` y `# @no-cookie-jar`, y cada petición autenticada lleva `# @no-cookie-jar` y `Cookie: {{login....response.headers.Set-Cookie}}`.
- **Por qué:** Es exactamente el mecanismo pedido en la issue #53 y permite intercalar peticiones de `admin`, `vendedor`, `ana` y `nuevo` sin re-autenticar ni mezclar cookies.
