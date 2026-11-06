# Librería (Parcial Programación III, caps. 1 a 6) — Base de Conocimiento

Base de conocimiento armada a partir de la consigna `Parcial_Cap1a6_Consigna.pdf` y del estado del repo y del tablero de GitHub (5 de noviembre de 2026).

**La consigna no se versiona** y estas fichas no la copian: resumen con otras palabras y citan la página (la del pie del PDF, "Página N de 24"). Ante cualquier duda, manda la consigna.

## Índice de Archivos

| Archivo | Contenido |
|---|---|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Qué es el parcial, objetivos por actor, alcance y lo que queda afuera |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack con versiones mínimas, arquitectura en capas y resumen de endpoints |
| [03_actores_y_roles.md](03_actores_y_roles.md) | ADMIN, VENDEDOR, CLIENTE y SISTEMA, matriz de permisos, rutas públicas, usuarios iniciales |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Tablas nuevas y cambios, ERD, invariante de stock, migraciones, datos iniciales |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | **RN-01 a RN-16** con su garante y quién las implementa |
| [06_funcionalidades.md](06_funcionalidades.md) | Los 10 ejercicios con puntaje, sus issues y los casos C y D |
| [07_flujos_principales.md](07_flujos_principales.md) | Petición autenticada, login, registro, venta, libros y roles, paso a paso |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, **estructura obligatoria contra el repo**, seguridad y variables de entorno |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Decisiones del grupo (migraciones, UoW, intento de acceso, tests, despliegue) y supuestos |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Lo que no coincide con la consigna y lo que falta decidir |
| [11_entrega_y_despliegue.md](11_entrega_y_despliegue.md) | El `.zip` con `parcial/` y `despliegue/`, imagen, VPS y `DEPLOY.md` |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)
7. Antes de entregar → [11](11_entrega_y_despliegue.md)

## Resumen Ejecutivo

La librería del TP suma usuarios con roles vigentes (autorización consultada en la base en cada petición), repositorios con Unit of Work (una transacción por operación de negocio) y stock que sólo cambia por movimientos de sólo agregado. Aparte, el TP de los capítulos 1 a 4 se despliega en el VPS dentro de un contenedor.
