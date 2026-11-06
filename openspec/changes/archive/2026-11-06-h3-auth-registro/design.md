# Design: h3-auth-registro

## UI Mockups

Decision: no (no UI)

## Context

El registro de clientes por la web (`POST /auth/registro`) requiere coordinar dos agregados de dominio (`Usuario` y `Cliente`) y una relación intermedia (`AsignacionRol`). Ver `proposal.md` para motivación y reglas RN-01 y RN-02.

## Goals / Non-Goals

**Goals:**
- Ejecutar el auto-registro de forma 100% atómica en un único bloque `async with uow`.
- Prevenir el bloqueo del event loop calculando bcrypt fuera de la transacción.
- Garantizar que si un cliente o usuario con ese email ya existe, la base rechace la escritura por unicidad y el UoW revierta toda la transacción sin dejar filas sueltas ni modificar el cliente previo (caso C-02).
- Validar rigurosamente los campos con `extra="forbid"` y longitud máxima de contraseña de 72 bytes.

**Non-Goals:**
- No emite cookie de sesión ni inicia sesión automáticamente (el flujo de login es posterior e independiente).
- No gestiona asignación de otros roles (`ADMIN` o `VENDEDOR`), que permanecen restringidos al administrador en rutas protegidas.

## Decisions

### 1. Hash de contraseña antes de abrir la transacción
- **Decisión**: Se invoca `await hashear_password(datos.password, settings=settings)` antes del bloque `async with uow:`.
- **Razón**: Cumple la sección 5.6 de la consigna para no retener conexiones del pool durante los ~300 ms que toma bcrypt.

### 2. Composición de `ClienteRepository` en `UsuarioUnitOfWork`
- **Decisión**: Incorporar `self.clientes = ClienteRepository(session)` en `UsuarioUnitOfWork`.
- **Razón**: Sigue el patrón ya establecido en `VentaUnitOfWork` (que compone `LibroRepository`), permitiendo que el servicio de usuarios registre tanto el usuario como su ficha de cliente compartiendo la misma sesión y transacción.

### 3. Secuencia atómica de inserción en el Unit of Work
- **Decisión**:
  1. `uow.usuarios.add(usuario)`
  2. `await uow.session.flush()` (obtiene `usuario.id` y evalúa unicidad de `usuario.email`).
  3. `uow.asignaciones_rol.add(AsignacionRol(usuario_id=usuario.id, rol="CLIENTE", desde=ahora))`
  4. `uow.clientes.agregar(Cliente(nombre=datos.nombre, email=datos.email, usuario_id=usuario.id))`
  5. Al salir del bloque, `uow` confirma con `commit()`.
- **Alternativa descartada**: Realizar consultas previas `SELECT` para verificar si el email ya existe. Descartada porque la consigna explícitamente exige: "Unicidad garantizada por la base; no se verifica con una consulta previa" (págs. 20-21).

### 4. Manejo de conflictos de integridad (409)
- **Decisión**: Utilizar `uow.con_mensajes(unique="El correo ya se encuentra registrado")`.
- **Razón**: Si el email choca en `usuario` (en el flush) o en `cliente` (en el commit), el Unit of Work captura el `IntegrityError`, hace `rollback()` y lanza `Conflicto("El correo ya se encuentra registrado")`. El router traduce esto directamente a HTTP 409 con mensaje limpio sin trazas de la base (RN-15).

## Risks / Trade-offs

- **[Riesgo] Contraseñas mayores a 72 bytes provocan 500 en bcrypt**:
  → **Mitigación**: `PasswordBcrypt` valida `len(v.encode('utf-8')) <= 72` en el schema `RegistroRequest`, respondiendo 422 antes de invocar la lógica de negocio.
- **[Riesgo] Fila de usuario creada si la creación de cliente falla**:
  → **Mitigación**: Ambas escrituras viven en la misma sesión y transacción dentro del bloque `async with uow`; un fallo en la inserción de cliente revierte inmediatamente la transacción completa.
