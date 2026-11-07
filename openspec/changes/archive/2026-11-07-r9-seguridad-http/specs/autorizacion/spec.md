## ADDED Requirements

### Requirement: Casos de prueba ejecutables de autorización y seguridad (C-06 a C-09)
El sistema SHALL incluir el archivo `test/seguridad.http` con los casos C-06 (401 sin sesión contra 403 por rol insuficiente y acceso a lo propio), C-07 (revocación de rol con sesión abierta que corta el permiso en la petición siguiente), C-08 (autoprotección del rol `ADMIN` y validación de `vence_en`) y C-09 (cambio obligatorio de contraseña en el grupo protegido y habilitación tras cambiarla), ejecutables tras `python seed.py` utilizando `# @name` y `# @no-cookie-jar`.

#### Scenario: Ejecución de C-06 a C-09 con múltiples sesiones en REST Client
- **WHEN** se ejecuta `test/seguridad.http` después de `python seed.py`
- **THEN** cada petición documenta su código HTTP esperado (401, 403, 409, 422, 200, 201) y utiliza `# @no-cookie-jar` con `Cookie: {{loginX.response.headers.Set-Cookie}}` para aislar las sesiones de cada actor
