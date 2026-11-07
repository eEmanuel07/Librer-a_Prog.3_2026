# Proposal: h7-auth-http

## Why

La consigna del Parcial (págs. 21-23 y Ejercicio 4) exige un conjunto de casos de prueba mínimos organizados en archivos `.http` para ser ejecutados con la extensión REST Client de VS Code. Las funcionalidades de autenticación (H3, H4 y H6) ya se encuentran mergeadas en `main`. Esta propuesta formaliza la creación de `test/auth.http` cubriendo de manera exhaustiva y reproducible los casos **C-01 a C-05** y los endpoints complementarios de ciclo de sesión.

## What Changes

- Creación del archivo ejecutable `test/auth.http` parametrizado con `@base_url = http://localhost:8000`.
- Especificación de las peticiones HTTP documentando código esperado, cabeceras y cuerpo:
  - **C-01 (Entrada inválida):** Validación de contrato estricto rechazando tipos no conformes con HTTP 422 Unprocessable Entity, garantizando que nunca se produzca un error 500.
  - **C-02 (Auto-registro y no apropiación):** Demostración de `POST /auth/registro` exitoso (HTTP 201) y verificación de conflicto HTTP 409 ante correo existente de usuario o cliente sin alterar datos existentes.
  - **C-03 (Login con cookie HttpOnly):** Demostración de `POST /auth/login` con credenciales válidas emitiendo la cookie `access_token` con atributos `HttpOnly`, `SameSite=Lax`, sin exponer el JWT en la respuesta JSON.
  - **C-04 (Anti-enumeración):** Demostración de respuesta idéntica HTTP 401 y tiempo uniforme tanto si el correo no existe (hash ficticio RN-08) como si la contraseña es errónea.
  - **C-05 (Rate limiting):** Demostración de rechazo con HTTP 429 Too Many Requests y cabecera `Retry-After: 60` al superar el umbral de 5 fallos en 60 segundos por correo e IP (RN-07).
  - **Flujo de sesión y seguridad (H6):** Peticiones para `GET /auth/yo`, `POST /auth/cambiar-password` y `POST /auth/logout`.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None. (Este change incorpora suites de pruebas ejecutables sin alterar los requerimientos del sistema; se utiliza `skip_specs: true` en `.openspec.yaml`).

## Impact

- **Código:** Se agrega `test/auth.http`. No se modifica código de producción en `app/`.
- **Dependencias:** Requiere que el servidor local esté corriendo (`uvicorn app.main:app` o `uvicorn main:app`).
