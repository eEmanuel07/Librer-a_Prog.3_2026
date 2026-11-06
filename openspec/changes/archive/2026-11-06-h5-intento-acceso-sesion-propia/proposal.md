# Proposal: h5-intento-acceso-sesion-propia

> Issue: #41 ([H5] — intento_acceso en su propia sesión y transacción). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 7 (pág. 12) y Ejercicio 4 (pág. 11).

## Nota sobre el orden: change retroactivo

Este change se escribió **después** de la implementación. La separación de responsabilidades para el registro de intentos de acceso en su propia sesión y el conteo en una sola consulta ya estaban implementados, probados con tests y mergeados en `main` (PR #72) antes de inicializar OpenSpec en el repositorio.

## Why

El Ejercicio 7 establece que cada intento de login (correcto o fallido) debe anotarse en `intento_acceso` desde una sesión y una transacción propias que se confirman siempre (`commit()`), siendo la única escritura del sistema que no comparte la transacción de su petición para que los fallos sobrevivan al rollback. Debe incluir un comentario obligatorio de 3 partes explicando qué hace distinto, por qué y cuál es su costo. A la vez, para cumplir con "ningún repositorio confirma" (Ejercicio 6), `IntentoAccesoRepository` no debe recibir `session_factory` ni confirmar; la función `registrar_intento_acceso` vive en `unit_of_work.py`. Finalmente, el cálculo de fallos vigentes debe costar una sola consulta SQL utilizando una subconsulta escalar (`scalar_subquery`).

## What Changes

- **`app/modules/usuarios/repository.py` (`IntentoAccesoRepository`)**:
  - `contar_fallos_vigentes_y_primer_fallo(email, ip, desde)`: calcula en una única consulta SQL la cantidad de intentos fallidos desde el último login exitoso o la ventana temporal dada, devolviendo `(cantidad, primer_fallo)`.
  - El repositorio recibe únicamente la sesión de la petición y no ejecuta `commit()`.
- **`app/modules/usuarios/unit_of_work.py`**:
  - Función `registrar_intento_acceso(session_factory, email, ip, exito, cuando)`:
    - Abre una sesión propia (`async with session_factory() as sesion_propia:`).
    - Agrega la fila a `intento_acceso` y hace `await sesion_propia.commit()`.
    - Documenta el comentario de 3 partes exigido por la sección 6.8.1: qué hace distinto, por qué no comparte la transacción y cuál es su costo.
    - Utiliza `datetime.now(timezone.utc)` por defecto para evitar fechas sin zona horaria.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `autenticacion`: Incorpora las garantías de aislamiento transaccional y conteo optimizado en una sola consulta para la persistencia y evaluación de intentos de acceso.

## Impact

- **Persistencia:** Resistencia de la bitácora de intentos frente a excepciones o reversiones de negocio.
- **Rendimiento:** Evaluación del rate limit en una sola consulta a la base de datos sin recargar la CPU con bcrypt.
- **Arquitectura:** Estricto apego al principio de que ningún repositorio confirma sus transacciones.
