## ADDED Requirements

### Requirement: Dos grupos de rutas en main.py y bloqueo por cambio obligatorio de contraseña (RN-06, RN-14)
El sistema SHALL organizar las rutas en `app/main.py` en dos grupos (`grupo_abierto` y `grupo_protegido`), montando una sola vez en `grupo_protegido` la dependencia `verificar_cambio_password_pendiente` (`app/core/dependencies.py`) que responda HTTP 403 Forbidden cuando `usuario.debe_cambiar_password` sea verdadero, permitiendo únicamente el uso de `/auth` y de las rutas sin sesión hasta que el usuario actualice su contraseña.

#### Scenario: Usuario con cambio obligatorio de contraseña recibe 403 en rutas protegidas y 200 tras cambiarla (C-09)
- **WHEN** un usuario con `debe_cambiar_password = True` inicia sesión e intenta acceder a cualquier ruta del `grupo_protegido`
- **THEN** el sistema responde HTTP 403 Forbidden; al enviar `POST /auth/cambiar-password` (en `grupo_abierto`) responde HTTP 200 y, en la petición siguiente con la misma sesión, accede con HTTP 200 a las rutas permitidas del `grupo_protegido`

#### Scenario: Rutas propias solo requieren estar autenticado sin cambio pendiente (RN-14)
- **WHEN** un usuario autenticado con `debe_cambiar_password = False` (incluso con rol `CLIENTE`) consulta `GET /mis-ventas`
- **THEN** el sistema permite el acceso (HTTP 200) dentro del `grupo_protegido`
