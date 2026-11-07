# Spec Delta: autorizacion

## ADDED Requirements

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
