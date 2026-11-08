# autorizacion Specification

## Purpose
Definir el control de acceso basado en roles vigentes en la base de datos (RN-04), la separación en dos grupos de rutas para el cambio obligatorio de contraseña (RN-06), la gestión de roles con vigencia y autoprotección de administradores (RN-03, RN-05), el alta de personal y la consulta paginada de la bitácora de seguridad (RN-16).

## Requirements

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

### Requirement: Asignación de roles con vigencia opcional y validación de fecha futura con zona horaria
El sistema SHALL proveer el endpoint `POST /usuarios/{usuario_id}/roles` (exclusivo para `ADMIN`) que asigne un rol (`ADMIN`, `VENDEDOR` o `CLIENTE`) con fecha de vencimiento opcional (`vence_en`), validando en el contrato que `vence_en` incluya zona horaria y esté en el futuro (422 en caso contrario), cerrando la fila anterior si estaba vencida, rechazando con 409 si el rol ya está vigente (RN-03) y registrando un `EventoSeguridad` en la misma transacción (RN-16).

#### Scenario: Asignación de rol con vencimiento en el pasado o sin zona horaria responde 422 (C-07 / C-08)
- **WHEN** un administrador envía `POST /usuarios/{id}/roles` con `vence_en` sin zona horaria (naive) o con una fecha en el pasado
- **THEN** el sistema responde HTTP 422 Unprocessable Entity

#### Scenario: Reasignación de un rol vencido cierra la fila anterior y abre una nueva
- **WHEN** un usuario tiene una asignación de rol con `revocada_en IS NULL` pero `vence_en` en el pasado, y un administrador vuelve a asignarle ese mismo rol
- **THEN** el sistema cierra la fila anterior escribiendo `revocada_en`, crea una nueva fila abierta y registra el evento en `evento_seguridad` en la misma transacción, respondiendo 201

#### Scenario: Asignación duplicada de un rol vigente responde 409 (RN-03)
- **WHEN** un administrador intenta asignar un rol que el usuario ya tiene vigente
- **THEN** el sistema responde HTTP 409 Conflict sin crear filas nuevas

### Requirement: Revocación de roles sin borrar filas y autoprotección de administradores (RN-05)
El sistema SHALL proveer `DELETE /usuarios/{usuario_id}/roles/{rol}` y `GET /usuarios/{usuario_id}/roles` (exclusivos para `ADMIN`), donde revocar escriba `revocada_en` sin eliminar la fila, registre el evento en `evento_seguridad` en la misma transacción (RN-16), e impida con HTTP 409 que un administrador se revoque su propio rol `ADMIN` o que el sistema quede sin administradores vigentes (RN-05).

#### Scenario: Revocación de rol escribe revocada_en y conserva la fila (C-07)
- **WHEN** un administrador revoca el rol de otro usuario mediante `DELETE /usuarios/{id}/roles/{rol}`
- **THEN** la fila de `asignacion_rol` conserva su registro con `revocada_en` completado y se agrega una línea en `evento_seguridad` en el mismo bloque transaccional

#### Scenario: Administrador intenta revocarse su propio rol ADMIN y recibe 409 (C-08 / RN-05)
- **WHEN** un administrador autenticado envía `DELETE /usuarios/{su_propio_id}/roles/ADMIN`
- **THEN** el sistema responde HTTP 409 Conflict y el rol continúa vigente

### Requirement: Alta de personal con contraseña provisoria y evento de seguridad en la misma transacción (RN-16)
El sistema SHALL proveer el endpoint `POST /usuarios` (exclusivo para usuarios con rol `ADMIN` vigente) que cree una cuenta de personal con `activo = True` y `debe_cambiar_password = True`, calculando el hash bcrypt antes de abrir la transacción y registrando en el mismo bloque del Unit of Work una fila en `evento_seguridad` con el correo del administrador como `actor`, devolviendo HTTP 201 sin incluir `password_hash`.

#### Scenario: Administrador da de alta a un integrante del personal
- **WHEN** un administrador autenticado envía `POST /usuarios` con `nombre`, `email` y `password` válidos (hasta 72 bytes UTF-8)
- **THEN** el sistema crea el usuario con `debe_cambiar_password = True`, registra el evento en `evento_seguridad` en la misma transacción y responde HTTP 201 con los datos del usuario sin `password_hash`

#### Scenario: Alta de personal con correo duplicado responde 409 y no deja evento de seguridad (RN-01, RN-16)
- **WHEN** un administrador envía `POST /usuarios` con un `email` que ya pertenece a otro usuario
- **THEN** el sistema revierte la transacción, no deja registro en `evento_seguridad` y responde HTTP 409 Conflict con mensaje propio

#### Scenario: Usuario sin rol ADMIN recibe 403 al intentar dar de alta personal (C-06)
- **WHEN** un usuario autenticado sin rol `ADMIN` vigente envía `POST /usuarios`
- **THEN** el sistema responde HTTP 403 Forbidden

### Requirement: Consulta paginada del historial de seguridad (RN-16)
El sistema SHALL proveer el endpoint `GET /eventos` (exclusivo para usuarios con rol `ADMIN` vigente) que devuelva las filas de `evento_seguridad` dentro del envoltorio de paginación `{items, total, page, size, pages}`, respondiendo HTTP 422 si se solicita una página inexistente y HTTP 403 si el usuario no posee el rol `ADMIN`.

#### Scenario: Administrador consulta el historial de seguridad paginado
- **WHEN** un administrador autenticado envía `GET /eventos?page=1&size=20`
- **THEN** el sistema responde HTTP 200 con `{items, total, page, size, pages}` listando las altas de personal, asignaciones/revocaciones de rol, cambios de contraseña y eventos del sistema

#### Scenario: Página más allá de la última en GET /eventos responde 422
- **WHEN** un administrador solicita una página mayor a `pages` en `GET /eventos`
- **THEN** el sistema responde HTTP 422 Unprocessable Entity

#### Scenario: Usuario sin rol ADMIN recibe 403 en GET /eventos
- **WHEN** un usuario autenticado sin rol `ADMIN` vigente envía `GET /eventos`
- **THEN** el sistema responde HTTP 403 Forbidden

### Requirement: Protección RBAC y paginación con envoltorio en editoriales, géneros y autores
El sistema SHALL exigir el rol `ADMIN` vigente (`Depends(requiere_rol("ADMIN"))`) en todas las operaciones de escritura (`POST` y `PATCH`) de `editoriales`, `generos` y `autores`, mantener públicas sus lecturas (`GET`), devolver todos sus listados con el envoltorio `{items, total, page, size, pages}` de `app/core/paginacion.py`, y excluir los libros dados de baja (`borrado_en IS NOT NULL`, RN-13) de los listados `/{id}/libros`.

#### Scenario: Vendedor intenta crear o modificar editorial, género o autor y recibe 403 (C-06)
- **WHEN** un usuario autenticado con rol `VENDEDOR` (sin rol `ADMIN` vigente) envía `POST` o `PATCH` a `/editoriales`, `/generos` o `/autores`
- **THEN** el sistema responde HTTP 403 Forbidden sin realizar cambios

#### Scenario: Visitante sin sesión consulta listados del catálogo y recibe el envoltorio de paginación
- **WHEN** un visitante sin sesión envía `GET /editoriales`, `GET /generos` o `GET /editoriales/{id}/libros`, `GET /generos/{id}/libros`, `GET /autores/{id}/libros`
- **THEN** el sistema responde HTTP 200 con `{items, total, page, size, pages}` excluyendo los libros dados de baja

### Requirement: Dos grupos de rutas en main.py y bloqueo por cambio obligatorio de contraseña (RN-06, RN-14)
El sistema SHALL organizar las rutas en `app/main.py` en dos grupos (`grupo_abierto` y `grupo_protegido`), montando una sola vez en `grupo_protegido` la dependencia `verificar_cambio_password_pendiente` (`app/core/dependencies.py`) que responda HTTP 403 Forbidden cuando `usuario.debe_cambiar_password` sea verdadero, permitiendo únicamente el uso de `/auth` y de las rutas sin sesión hasta que el usuario actualice su contraseña.

#### Scenario: Usuario con cambio obligatorio de contraseña recibe 403 en rutas protegidas y 200 tras cambiarla (C-09)
- **WHEN** un usuario con `debe_cambiar_password = True` inicia sesión e intenta acceder a cualquier ruta del `grupo_protegido`
- **THEN** el sistema responde HTTP 403 Forbidden; al enviar `POST /auth/cambiar-password` (en `grupo_abierto`) responde HTTP 200 y, en la petición siguiente con la misma sesión, accede con HTTP 200 a las rutas permitidas del `grupo_protegido`

#### Scenario: Rutas propias solo requieren estar autenticado sin cambio pendiente (RN-14)
- **WHEN** un usuario autenticado con `debe_cambiar_password = False` (incluso con rol `CLIENTE`) consulta `GET /mis-ventas`
- **THEN** el sistema permite el acceso (HTTP 200) dentro del `grupo_protegido`

### Requirement: Casos de prueba ejecutables de autorización y seguridad (C-06 a C-09)
El sistema SHALL incluir el archivo `test/seguridad.http` con los casos C-06 (401 sin sesión contra 403 por rol insuficiente y acceso a lo propio), C-07 (revocación de rol con sesión abierta que corta el permiso en la petición siguiente), C-08 (autoprotección del rol `ADMIN` y validación de `vence_en`) y C-09 (cambio obligatorio de contraseña en el grupo protegido y habilitación tras cambiarla), ejecutables tras `python seed.py` utilizando `# @name` y `# @no-cookie-jar`.

#### Scenario: Ejecución de C-06 a C-09 con múltiples sesiones en REST Client
- **WHEN** se ejecuta `test/seguridad.http` después de `python seed.py`
- **THEN** cada petición documenta su código HTTP esperado (401, 403, 409, 422, 200, 201) y utiliza `# @no-cookie-jar` con `Cookie: {{loginX.response.headers.Set-Cookie}}` para aislar las sesiones de cada actor
