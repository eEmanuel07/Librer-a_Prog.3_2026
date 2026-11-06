# autenticacion Specification

## Purpose
Garantiza el aislamiento transaccional del registro de intentos de acceso y la eficiencia del conteo de fallos vigentes.

## ADDED Requirements

### Requirement: Aislamiento transaccional en registro de intentos de acceso
El sistema SHALL registrar cada intento de acceso en una sesión y transacción propias e independientes que se confirman inmediatamente con `commit()`, asegurando que el intento persista aunque la petición principal sea rechazada o revertida.

#### Scenario: Persistencia del intento ante rollback de la petición
- **WHEN** un intento de acceso falla o una transacción de petición revierte con ROLLBACK
- **THEN** la fila correspondiente en `intento_acceso` permanece confirmada en la base de datos

#### Scenario: Documentación de aislamiento en el código
- **WHEN** se inspecciona la función `registrar_intento_acceso`
- **THEN** incluye el comentario obligatorio que explica qué hace distinto, por qué no puede compartir la transacción y cuál es su costo

### Requirement: Conteo de fallos vigentes en una única consulta SQL
El método `contar_fallos_vigentes_y_primer_fallo` de `IntentoAccesoRepository` SHALL evaluar la cantidad de fallos y el instante del primer fallo en una sola consulta SQL utilizando una subconsulta escalar para el último intento exitoso.

#### Scenario: Conteo posterior al último éxito en una sola consulta
- **WHEN** se invoca `contar_fallos_vigentes_y_primer_fallo` para un correo e IP dados
- **THEN** la base ejecuta una única sentencia SELECT devolviendo el recuento de fallos posteriores al último éxito dentro de la ventana
