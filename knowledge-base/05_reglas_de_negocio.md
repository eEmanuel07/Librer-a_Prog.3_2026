# Reglas de Negocio

Las reglas del parcial se **numeran de nuevo** y reemplazan a las del TP donde se superponen (págs. 6-8). Siguen vigentes, aunque no se repitan, los CHECK de precio y stock del libro y la búsqueda por título con parámetros ligados (pág. 6).

> **Ojo con la numeración:** varios comentarios del código todavía usan los números del TP viejo. Por ejemplo, el "RN-10" de `app/core/pagination.py` es la paginación del TP, no la venta con stock del parcial. En código, PR, issues y specs se usa **siempre la numeración de esta tabla**.

## Tabla de reglas (págs. 7-8)

El **garante** es el mecanismo que la consigna espera para cumplir la regla. **Quién** sale del tablero de GitHub (issue y responsable).

| Regla | Enunciado (resumido) | Garante esperado | Quién (tablero) |
|---|---|---|---|
| **RN-01** | Son únicos el correo de un usuario, el de un cliente, el nombre de una editorial y el de un género. El ISBN es único entre los libros **no** dados de baja. | UNIQUE e índice único parcial en la base; 409 con mensaje propio | Esquema: B6 (Belén) con los modelos de H1 y E1. Traducción a 409: B4 (Belén) |
| **RN-02** | El auto-registro crea el usuario, su rol CLIENTE y su ficha de cliente: o las tres filas o ninguna. Si ya hay un cliente con ese correo, 409 y no se apropia de la ficha. | Un solo Unit of Work | H3 (Hernán) |
| **RN-03** | Un usuario tiene a lo sumo una asignación abierta por rol. | Índice único parcial; 409 | Índice: B6 / H1. 409 al asignar: R5 (Bruno) |
| **RN-04** | Los permisos se deciden con los roles vigentes **en la base**, en cada petición; los del token son informativos. | Dependencia que consulta `asignacion_rol` | R2 (Bruno) |
| **RN-05** | Un administrador no puede revocarse su propio ADMIN, y el sistema nunca queda sin administradores vigentes. | Comprobación en el servicio; 409 | R5 (Bruno) |
| **RN-06** | Con el cambio de contraseña pendiente, sólo se usan `/auth` y las rutas que no piden sesión. | Dos grupos de rutas; 403 | R3 (Bruno) |
| **RN-07** | Tras 5 fallos con el mismo correo desde la misma IP en 60 s, el login da 429 sin verificar la contraseña. Un login correcto reinicia la cuenta (los fallos quedan en la tabla, pero dejan de contar). | Conteo sobre `intento_acceso`; `Retry-After` | H4 (Hernán), con H5 (sesión propia del intento) |
| **RN-08** | El login responde lo mismo, y tarda lo mismo, exista o no el correo. | Mismo mensaje; verificación contra un hash ficticio | H4 (Hernán) |
| **RN-09** | La venta nace con sus renglones (al menos uno, sin libros repetidos), con el precio copiado del libro y el total calculado por el servidor. Las ventas no se modifican. | DTO: precio y total nunca viajan en el cuerpo; no hay PATCH | J3 (Joaquín) |
| **RN-10** | Registrar una venta descuenta el stock de cada libro y deja un movimiento por renglón. Si un libro no alcanza, no queda **ninguna** escritura (venta, renglones, descuentos ni movimientos). | Un solo Unit of Work; 409 | J3 (Joaquín) |
| **RN-11** | El stock sólo cambia con movimientos: alta con stock inicial, reposición y venta. No se edita por PATCH. | Punto único de escritura de stock | E3 (Elías, hecho), usado por E4, E5 y J3 |
| **RN-12** | `movimiento_stock` es de sólo agregado: nadie modifica ni borra sus filas. | Disparador en la base, instalado por migración | E6 (Elías); caso C-14 en E7 |
| **RN-13** | Un libro dado de baja sale del catálogo y no se vende ni se repone, pero sus datos se conservan y las ventas viejas lo siguen mostrando. | Borrado lógico; 409 | E4 / E5 (Elías), con E1 y E2 (hechas) |
| **RN-14** | Lo propio sólo pide estar autenticado: un cliente ve sus ventas y ninguna otra. | `/mis-ventas` y comprobación de dueño; 403 | J6 y J5 (Joaquín); R3 lo nombra para el grupo protegido |
| **RN-15** | Ningún error devuelve texto interno de la base, y ninguna entrada inválida termina en 500. | Traducción del `IntegrityError`; validación en el contrato | Transversal: B4 (traducción en el UoW) y los contratos de cada módulo. Revisión final: H8 (Hernán) |
| **RN-16** | Cada alta de personal, cambio de rol y cambio de contraseña deja una línea en `evento_seguridad` **en la misma transacción**. | Un solo Unit of Work | R4 y R5 (Bruno); H6 para el cambio de contraseña. Línea `SISTEMA` del seed: R8 (Bruno) |

## Reglas que el Ej. 6 pide en un solo bloque `async with` (pág. 12)

RN-02, RN-10 y RN-16: cada operación se escribe completa dentro de **un** bloque del Unit of Work. La lectura posterior, si la hay, va en otro bloque y no escribe.

## Excepciones globales (requisitos no funcionales, págs. 20-21)

- **Unicidad:** la garantiza la base; no se consulta antes de escribir.
- **Errores:** mensajes propios; nunca el texto de la base ni una traza; ninguna entrada inválida en 500.
- **SQL:** nunca armado por concatenación con datos del usuario.
- **Credenciales:** ninguna contraseña ni clave de firma en el código (tampoco como valor por defecto), en `alembic.ini`, en el repositorio ni en la imagen.
- **Token:** sólo en la cookie `HttpOnly`; nunca en el cuerpo ni leído de `Authorization`.
- **Transacciones:** ningún repositorio confirma; ningún servicio construye su UoW; el UoW no cierra la sesión.
- **Carga perezosa:** prohibida; toda relación que se lee se precarga en el repositorio.
- **Única excepción a "una transacción por petición":** el registro de `intento_acceso`, que usa sesión y transacción propias para sobrevivir al rollback del login fallido (pág. 12).
