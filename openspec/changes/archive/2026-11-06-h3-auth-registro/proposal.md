# Proposal: h3-auth-registro

> Issue: #39 ([H3] — POST /auth/registro). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 4 (pág. 11), Ejercicio 6 (pág. 12), RN-01, RN-02 y caso C-02 (pág. 21).

## Why

Actualmente los clientes sólo pueden ser creados por personal administrativo o de ventas desde rutas protegidas. El Ejercicio 4 y la regla RN-02 exigen que los visitantes puedan auto-registrarse en la web a través de `POST /auth/registro`. Esta operación debe crear atómicamente el usuario, su rol `CLIENTE` y su ficha de cliente en un único `UnitOfWork` (o quedan las tres filas o ninguna). Además, si ya existe un cliente o usuario con ese correo electrónico, debe responder 409 con mensaje propio sin dejar filas huérfanas ni apropiarse de la ficha existente (caso C-02).

## What Changes

- **Contratos de entrada y salida (`app/modules/usuarios/schemas.py`)**:
  - `RegistroRequest`: contrato estricto (`extra="forbid"`) con `nombre` (no vacío), `email` (normalizado en minúsculas y sin espacios) y `password` restringida a 1-72 bytes UTF-8 (`PasswordBcrypt`).
  - `RegistroResponse`: contrato de respuesta 201 con `id`, `email`, `nombre`, `cliente_id` y `mensaje`, sin incluir nunca `password_hash`.
- **Composición en `UsuarioUnitOfWork` (`app/modules/usuarios/unit_of_work.py`)**:
  - Incorporar `self.clientes = ClienteRepository(session)` al Unit of Work de usuarios para posibilitar la escritura atómica coordinada de usuarios y clientes en la misma transacción.
- **Lógica de negocio en `app/modules/usuarios/service.py`**:
  - Función `registrar(datos, uow, settings)`:
    - Calcula el hash de la contraseña **antes** de abrir la transacción con `hashear_password` (fuera del bucle de eventos y bajo semáforo).
    - En un **único bloque** `async with uow.con_mensajes(unique="El correo electrónico ya está registrado"):` crea:
      1. `Usuario(nombre=datos.nombre, email=datos.email, password_hash=hash, activo=True, debe_cambiar_password=False)`
      2. `AsignacionRol(usuario_id=usuario.id, rol="CLIENTE", desde=ahora)`
      3. `Cliente(nombre=datos.nombre, email=datos.email, usuario_id=usuario.id)`
    - Si la base rechaza por duplicado de email (en `usuario` o en `cliente`), el `UnitOfWork` ejecuta `rollback()` y traduce a `Conflicto` (409) con mensaje propio.
- **Ruta HTTP en `app/modules/usuarios/router.py`**:
  - Endpoint `POST /auth/registro` (grupo abierto, sin sesión requerida), con código de estado HTTP 201 Created.
  - Atrapa `Conflicto` y responde 409 con el mensaje de dominio.

## Capabilities

### New Capabilities

(ninguna nueva)

### Modified Capabilities

- `autenticacion`: Incorpora los requisitos y escenarios para el auto-registro atómico de usuarios/clientes y el control de unicidad.

## Impact

- **Seguridad:** El hash bcrypt se calcula antes de abrir la transacción, liberando la conexión del pool durante el cálculo. Contrato estricto `extra="forbid"` impide que nadie se auto-asigne roles como `ADMIN`.
- **Transacciones:** Garantía atómica de RN-02: o persisten `usuario`, `asignacion_rol` y `cliente`, o no persiste ninguna.
- **Rutas:** Endpoint expuesto en `POST /auth/registro`.
