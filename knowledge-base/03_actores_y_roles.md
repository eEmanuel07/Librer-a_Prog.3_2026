# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa |
|---|---|---|
| Visitante | Sin sesión | Grupo abierto: catálogo, registro y login (pág. 16) |
| `ADMIN` | Administrador | Catálogo, stock, personal, roles e historial de seguridad (págs. 3, 17) |
| `VENDEDOR` | Personal de mostrador | Ventas y clientes (págs. 3, 17-18) |
| `CLIENTE` | Cliente con acceso web; se auto-registra | Sus propias ventas (`/mis-ventas`, detalle propio) (págs. 3, 18) |
| `SISTEMA` | Actor de texto, **no** es un usuario | Firma la línea "Carga de los datos iniciales" en `evento_seguridad` (págs. 11, 20) |

Un usuario puede tener varios roles a la vez. Un cliente puede no tener usuario (el que atiende el mostrador) o tener a lo sumo uno (págs. 2, 5).

## Cómo se decide un permiso

- Los roles **no** son una columna de `usuario`: son las filas vigentes de `asignacion_rol`, las no revocadas y sin vencer (pág. 6).
- `get_usuario_actual` lee la cookie `access_token`. Responde **401** si no hay cookie, si el token es inválido o venció, o si el usuario no existe o está inactivo (pág. 11).
- `requiere_rol` consulta los roles vigentes **en la base en cada petición** y responde **403** (RN-04, pág. 11). Los roles del token son informativos. Revocar un rol corta el permiso de una sesión ya abierta.
- Con el cambio de contraseña pendiente, el usuario sólo usa `/auth` y las rutas abiertas: el resto da 403 (RN-06, págs. 7, 11).
- Lo propio sólo pide estar autenticado (RN-14, pág. 8).

## RBAC — Matriz de permisos (págs. 16-18)

| Recurso | Visitante | CLIENTE | VENDEDOR | ADMIN |
|---|---|---|---|---|
| Catálogo (libros, editoriales, géneros, autores), lectura | R | R | R | R |
| Catálogo, alta / PATCH / baja | — | — | — | CRUD |
| Reposición y movimientos de un libro | — | — | — | C, R |
| Usuarios del personal y roles | — | — | — | C, R, revocar |
| Eventos de seguridad | — | — | — | R |
| Clientes y perfiles | — | — | C, R, U | C, R, U |
| Ventas: alta y listado general | — | — | C, R | C, R |
| Detalle de una venta | — | R (sólo la propia) | R | R |
| `/mis-ventas` | — | R | R | R |
| `/auth/yo`, `/auth/cambiar-password`, `/auth/logout` | logout | sí | sí | sí |

R = leer, C = crear, U = modificar. Autoprotección: un ADMIN no puede revocarse su propio rol ADMIN y nunca puede quedar el sistema sin administradores (RN-05).

## Rutas públicas

`GET /health/live`, `GET /health/ready`, `POST /auth/registro`, `POST /auth/login`, `POST /auth/logout`, las de `/auth` con sesión (`GET /auth/yo`, `POST /auth/cambiar-password`) y todas las lecturas del catálogo (`/libros`, `/editoriales`, `/generos`, `/autores/{id}/libros` y sus detalles) (pág. 16).

## Usuarios iniciales (`seed.py`, págs. 19-20)

`admin@example.com` y `admin2@example.com` (ADMIN), `vendedor@example.com` (VENDEDOR), `ana@example.com` (CLIENTE, vinculada a la clienta Ana Paz) y `nuevo@example.com` (VENDEDOR con cambio de contraseña obligatorio). Las contraseñas son de prueba y viven sólo en `seed.py`.
