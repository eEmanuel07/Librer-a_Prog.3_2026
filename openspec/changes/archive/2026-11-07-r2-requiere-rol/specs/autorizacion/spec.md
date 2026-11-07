# Spec Delta: autorizacion

## ADDED Requirements

### Requirement: Verificación de roles vigentes en la base de datos en cada petición (RN-04)
El sistema SHALL proveer la fábrica de dependencias `requiere_rol(*roles_permitidos: str)` en `app/core/dependencies.py` que, apoyándose en `get_usuario_actual` y compartiendo la sesión de `get_session`, consulte en la base de datos las asignaciones de rol vigentes (no revocadas y no vencidas) del usuario en cada petición, respondiendo HTTP 403 Forbidden si el usuario no posee ninguno de los roles requeridos, o devolviendo la instancia de `Usuario` si posee al menos uno.

#### Scenario: Usuario con rol vigente accede a la ruta
- **WHEN** un usuario autenticado y activo tiene en la base una asignación vigente del rol requerido por la ruta
- **THEN** `requiere_rol` permite el paso y devuelve la instancia de `Usuario`

#### Scenario: Usuario autenticado sin el rol requerido recibe 403 (C-06)
- **WHEN** un usuario autenticado y activo intenta acceder a una ruta protegida con `requiere_rol` sin tener ese rol vigente en la base
- **THEN** el sistema responde HTTP 403 Forbidden

#### Scenario: Rol revocado o vencido con la sesión abierta responde 403 en la petición siguiente (C-07)
- **WHEN** un usuario inició sesión cuando tenía un rol vigente (por lo que el rol figura en su JWT), pero luego la asignación se revoca (`revocada_en` no nulo) o vence (`vence_en` en el pasado) en la base de datos
- **THEN** en la petición siguiente con la misma cookie `access_token`, el sistema consulta la base y responde HTTP 403 Forbidden

#### Scenario: Ruta que admite cualquiera de varios roles
- **WHEN** una ruta se protege con `requiere_rol("VENDEDOR", "ADMIN")`
- **THEN** tanto un usuario con rol `VENDEDOR` vigente como uno con rol `ADMIN` vigente acceden, mientras que un usuario solo con rol `CLIENTE` recibe HTTP 403 Forbidden
