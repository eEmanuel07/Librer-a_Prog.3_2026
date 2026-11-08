# Spec Delta: ventas

## ADDED Requirements

### Requirement: Registrar y listar todas las ventas con requiere_rol
El sistema SHALL proteger `POST /ventas` y `GET /ventas` con `requiere_rol("VENDEDOR", "ADMIN")`. El detalle (`GET /ventas/{id}`) y `GET /mis-ventas` no lo usan.

#### Scenario: Un cliente intenta registrar una venta
- **WHEN** Ana Paz (CLIENTE) envía `POST /ventas`
- **THEN** el sistema responde 403 «No tiene permisos para realizar esta acción» y no escribe nada

#### Scenario: Un cliente pide todas las ventas
- **WHEN** Ana Paz (CLIENTE) pide `GET /ventas`
- **THEN** el sistema responde 403 «No tiene permisos para realizar esta acción»
