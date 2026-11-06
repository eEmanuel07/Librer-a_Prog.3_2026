# transacciones Specification

## Purpose

Define cómo se confirma o revierte la escritura de cada petición de la API, cómo se informa al cliente cuando la base la rechaza, y que cada petición trabaja sobre una sola sesión y una sola conexión a la base.

## Requirements

### Requirement: Confirmación al terminar sin error
Una operación de escritura que termina sin error SHALL quedar confirmada en la base antes de que la API responda con éxito.

#### Scenario: Alta confirmada
- **WHEN** se da de alta una editorial con datos válidos y la API responde 201
- **THEN** una lectura posterior, en otra petición, devuelve esa editorial

#### Scenario: Modificación confirmada
- **WHEN** se modifica un cliente con PATCH y la API responde 200
- **THEN** una lectura posterior, en otra petición, devuelve el dato modificado

### Requirement: Reversión ante cualquier error
Si una operación falla por cualquier motivo (error de negocio, rechazo de la base o error inesperado), ninguna de sus escrituras SHALL quedar en la base.

#### Scenario: Venta con cliente inexistente
- **WHEN** se intenta crear una venta para un cliente que no existe
- **THEN** la API responde 409 y no queda en la base ni la venta ni sus renglones

#### Scenario: Error de negocio después de escribir
- **WHEN** un service ya agregó filas y después lanza un error de dominio antes de terminar
- **THEN** esas filas no quedan confirmadas

### Requirement: Rechazo de la base traducido a 409 con mensaje propio
Cuando la base rechaza una escritura por unicidad, clave foránea o CHECK, la API SHALL responder 409 con el mensaje propio de esa operación y SHALL NOT devolver texto interno de la base. Esto vale tanto si el rechazo ocurre durante la operación como al confirmarla.

#### Scenario: Unicidad
- **WHEN** se da de alta una editorial con un nombre que ya existe
- **THEN** la API responde 409 con el mensaje propio de editorial repetida

#### Scenario: Clave foránea
- **WHEN** se da de alta un libro con una editorial que no existe
- **THEN** la API responde 409 con el mensaje propio de referencia inexistente del libro

#### Scenario: CHECK
- **WHEN** la base rechaza una escritura por una restricción CHECK
- **THEN** la API responde 409 con el mensaje propio de reglas violadas de esa operación

#### Scenario: Rechazo durante la operación
- **WHEN** la base rechaza la escritura en un flush intermedio, antes de confirmar
- **THEN** la API responde 409 con el mismo mensaje propio y no queda nada escrito

#### Scenario: Sin texto interno
- **WHEN** cualquier escritura termina en 409 por un rechazo de la base
- **THEN** el cuerpo de la respuesta no contiene nombres de tablas, de restricciones ni trazas

### Requirement: Una sola sesión y una sola conexión por petición
Dentro de una petición, el Unit of Work y cualquier otra dependencia que pida la sesión SHALL recibir la misma sesión, de modo que la petición tome a lo sumo una conexión del pool. La única excepción permitida es el registro de intentos de acceso del login, que usa una sesión propia.

#### Scenario: Dependencia de autenticación y Unit of Work
- **WHEN** una ruta recibe un Unit of Work y además una dependencia que pide la sesión (como lo hará la del usuario actual)
- **THEN** las dos reciben el mismo objeto de sesión y la petición abre una sola sesión

#### Scenario: Petición común
- **WHEN** se atiende cualquier petición de los módulos editoriales, géneros, autores, libros, clientes o ventas
- **THEN** se crea una sola sesión para toda la petición

### Requirement: Contratos HTTP sin cambios
La reorganización del Unit of Work SHALL NOT cambiar los códigos de estado ni los mensajes que hoy devuelve la API.

#### Scenario: Pruebas manuales existentes
- **WHEN** se ejecutan las peticiones de los archivos `.http` de `test/`
- **THEN** cada una devuelve el mismo código y el mismo mensaje que antes del cambio
