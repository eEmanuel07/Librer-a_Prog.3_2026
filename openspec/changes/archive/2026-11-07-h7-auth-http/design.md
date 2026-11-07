# Design: h7-auth-http

## Context

El módulo de autenticación cuenta con todos sus endpoints implementados en `app/modules/usuarios/router.py`:
- `POST /auth/registro` (H3, RN-02)
- `POST /auth/login` (H4, RN-07, RN-08)
- `POST /auth/logout` (H6)
- `GET /auth/yo` (H6, RN-04)
- `POST /auth/cambiar-password` (H6, RN-16)

La consigna del parcial (págs. 21-23) estipula la verificación manual asistida por archivos `.http` mediante la extensión REST Client de Visual Studio Code.

## UI Mockups

Decision: no (no UI)

## Goals / Non-Goals

**Goals:**
- Proveer un archivo `test/auth.http` autocontenido, legible y fácilmente ejecutable.
- Demostrar los 5 casos canónicos de autenticación solicitados por la cátedra:
  - **C-01:** Entrada inválida -> 422 (nunca 500).
  - **C-02:** Auto-registro exitoso (201) y detección de duplicado / prevención de apropiación de fichas (409).
  - **C-03:** Login exitoso con cookie `HttpOnly` y body sin token expuesto (200).
  - **C-04:** Anti-enumeración: respuesta idéntica y tiempo uniforme ante contraseña mala o correo inexistente (401).
  - **C-05:** Límite de tasa: bloqueo con 429 Too Many Requests y cabecera `Retry-After: 60` tras 5 intentos erróneos.
- Incluir casos de verificación para `GET /auth/yo`, `POST /auth/cambiar-password` y `POST /auth/logout`.

**Non-Goals:**
- No modifica código de producción en `app/`.
- No sustituye los tests automatizados de integración y unitarios existentes en `tests/`.

## Decisions

### Decisión 1: Formato estándar REST Client
- Definición de variables globales en la cabecera del archivo:
  ```http
  @baseUrl = http://localhost:8000
  @contentType = application/json
  ```
- Separación de bloques con `###` y comentarios descriptivos con el código esperado.
- Uso de `# @name login` para peticiones que generan sesión y verificación de cookie en llamadas subsiguientes (`GET /auth/yo`).

### Decisión 2: Aislamiento del caso C-05 (Rate Limiting)
- Para evitar que la prueba de 5 intentos fallidos bloquee al usuario de prueba general por 60 segundos, el caso C-05 empleará un correo exclusivo para esa prueba (ej. `bruteforce@ejemplo.com`), permitiendo probar C-03 y C-04 sin demoras artificiales.

## Risks / Trade-offs

- **[Riesgo: Bloqueo transitorio por rate-limit]** → *Mitigación:* Separar credenciales entre los casos de prueba de éxito (C-03) y los de saturación de intentos (C-05).
- **[Riesgo: Dependencia de datos iniciales en base de datos]** → *Mitigación:* Diseñar C-02 y C-03 de manera que el flujo pueda auto-abastecerse (ej. registrando un cliente y luego iniciando sesión con ese mismo usuario) o utilizando los datos que dejará el seed de Bruno.
