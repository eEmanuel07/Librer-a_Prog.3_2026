# Visión y Objetivos

> Fuente: consigna `Parcial_Cap1a6_Consigna.pdf` (no se versiona; la tiene cada integrante). Las páginas citadas son las del pie del PDF ("Página N de 24"). Todo está resumido, no copiado.

## Propósito del sistema

API asincrónica de una **librería** que, sobre el TP de los capítulos 1 a 4 (catálogo, clientes y ventas), agrega **acceso con usuarios y roles**, una **capa de repositorios con Unit of Work** para que cada operación de negocio sea una sola transacción, y, aparte, el **despliegue del TP 1-4 en el VPS** dentro de un contenedor (págs. 1-2).

La librería abre el sistema a su personal y a sus clientes: el catálogo es público, el personal opera con roles y los clientes se registran solos para ver sus compras (pág. 3).

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| Visitante (sin sesión) | Consultar el catálogo de libros | Registrarse como cliente, iniciar sesión |
| ADMIN | Mantener el catálogo y el stock | Dar de alta personal, asignar y revocar roles con vigencia, ver el historial de seguridad |
| VENDEDOR | Registrar ventas en el mostrador | Atender clientes (alta, perfil, consulta de sus ventas) |
| CLIENTE | Ver sus propias compras | Ver el detalle de una venta propia |

(pág. 3; endpoints en págs. 16-18)

## Objetivos de aprendizaje que el parcial evalúa (pág. 1)

1. API en capas Router → Service → UoW → Repository → Model.
2. Evolucionar el esquema con Alembic: una migración autogenerada y leída, otra a mano.
3. Autenticación con bcrypt y token en cookie `HttpOnly`, sin bloquear el servidor y sin revelar qué cuentas existen.
4. Autorización consultando los roles vigentes en la base en cada petición, distinguiendo 401 de 403.
5. Una sola transacción por operación de negocio: un fallo a mitad no deja datos sueltos.
6. Delegar en la base lo que la base garantiza (unicidad entre vigentes, FK, CHECK, sólo agregado).
7. Imagen de Docker del TP 1-4 en línea en el VPS, sin filtrar secretos.

## Alcance del parcial

- Módulos `health`, `usuarios`, `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas` (pág. 9).
- Tablas nuevas de acceso y de movimientos de stock; cambios en `cliente` y `libro` (págs. 2, 4-6).
- Reglas de negocio RN-01 a RN-16 (págs. 7-8) → ver [05](05_reglas_de_negocio.md).
- Diez ejercicios con puntaje (págs. 9-16) → ver [06](06_funcionalidades.md).
- Entrega en un `.zip` con `parcial/` y `despliegue/` (pág. 24) → ver [11](11_entrega_y_despliegue.md).

## Fuera de alcance

- **Concurrencia** (capítulo 7): dos ventas simultáneas del último ejemplar pueden pisarse (actualización perdida); se acepta (pág. 2).
- **Colas de tareas** (capítulo 8): el aviso del comprobante va con `BackgroundTasks` y se pierde si el proceso se reinicia (pág. 2).
- El segundo mecanismo de sólo agregado (permisos del rol de base) no se pide (pág. 12).
- El despliegue **no** lleva los cambios del parcial: es el TP 1-4 tal como se entregó (págs. 2, 14).

## Métricas de éxito

- Pasan los casos C-01 a C-16 (`.http` en `test/`) y D-01 a D-08 (en el VPS) (págs. 21-23).
- Criterios de corrección con su peso (págs. 23-24). Un proyecto que no levanta, que no crea su esquema con `alembic upgrade head` sobre una base vacía o que tiene credenciales reales no se corrige hasta que se arregle (pág. 24).
