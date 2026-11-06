# Modelo de Datos

Los nombres de tablas y columnas son **obligatorios**, porque los usan los casos de prueba y la corrección. Se pueden agregar columnas, pero no quitar ni renombrar las indicadas (pág. 4).

## Dominios

| Dominio | Tablas | Módulo |
|---|---|---|
| Acceso | `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad` | `usuarios` |
| Catálogo | `editorial`, `genero`, `autor`, `libro`, `libro_autor` | `editoriales`, `generos`, `autores`, `libros` |
| Stock | `movimiento_stock` | `libros` |
| Clientes | `cliente`, `perfil_cliente` | `clientes` |
| Ventas | `venta`, `renglon_venta` | `ventas` |

(Ubicación de cada modelo: pág. 9.) `editorial`, `genero`, `autor`, `libro_autor` y `perfil_cliente` **no cambian** respecto del TP (pág. 4).

## ERD (resumen; figura 1 de la pág. 5)

```
usuario 1 ──< asignacion_rol >── (otorgada_por) usuario
usuario 1 ──0..1 cliente 1 ──0..1 perfil_cliente
cliente 1 ──< venta 1 ──<◆ renglon_venta >── 1 libro
libro   1 ──< movimiento_stock >── 0..1 venta   (venta_id nulo: reposición o stock inicial)
usuario 1 ──< movimiento_stock                   (quién lo registró)
editorial 1 ──< libro >── 0..1 genero
libro >──< autor  (libro_autor, con rol y orden)
intento_acceso, evento_seguridad: sin relaciones con otras tablas
```

◆ = composición (el renglón nace con la venta). `movimiento_stock` es de **sólo agregado**, y lo protege un disparador (pág. 5).

## Entidades nuevas o que cambian (págs. 5-6)

### usuario
- `id`, `email`, `nombre`, `password_hash`, `activo`, `debe_cambiar_password`
- `email` UNIQUE. **No** tiene columna `rol`.

### asignacion_rol
- `id`, `usuario_id`, `rol`, `desde`, `vence_en` (nulo), `revocada_en` (nulo), `otorgada_por` (nulo)
- CHECK `rol` ∈ {ADMIN, VENDEDOR, CLIENTE}. Índice único parcial `(usuario_id, rol) WHERE revocada_en IS NULL`.
- Revocar escribe `revocada_en`; la fila no se borra nunca (historial) (pág. 6).

### intento_acceso
- `id`, `cuando`, `email`, `ip`, `exito`. Índice `(email, ip, cuando)`.

### evento_seguridad
- `id`, `cuando`, `actor` (texto), `accion`. Sin restricciones extra.

### movimiento_stock
- `id`, `libro_id`, `venta_id` (nulo), `usuario_id`, `cantidad`, `motivo`, `cuando`
- CHECK `cantidad <> 0`. Sólo agregado (sin UPDATE ni DELETE).

### cliente (cambia)
- Agrega `usuario_id`, nulo y UNIQUE. `email` sigue siendo UNIQUE.
- `Cliente.usuario` devuelve un objeto, no una lista (pág. 10).

### libro (cambia)
- Agrega `borrado_en` (con zona horaria, nulo): borrado lógico.
- El ISBN pasa de UNIQUE común a **índice único parcial `(isbn) WHERE borrado_en IS NULL`**. Siguen los CHECK `precio > 0` y `stock >= 0`.

## Reglas transversales del esquema (pág. 6)

- Toda fecha nueva es `timestamptz`. El dinero es `NUMERIC` en la base y `Decimal` en Python, nunca `float`.
- Cada FK nueva lleva un índice, porque PostgreSQL no lo crea solo.
- La navegación se declara en los dos extremos.
- **Invariante de stock:** para cada libro, `stock` es igual a la suma de `cantidad` de sus movimientos. Se verifica después de cada caso de venta.
- El esquema se crea sólo con Alembic, nunca con `create_all` (pág. 10).

## Migraciones (pág. 10; detalle en [09](09_decisiones_y_supuestos.md))

| # | Revisión | Contenido | Estado |
|---|---|---|---|
| 1 | `24071e705bcf` | Esquema del TP (`init_schemas`) | en `main` |
| 2 | `0efd84a6de03` | `genero` y `libro.genero_id` | en `main` |
| 3 | `4a775b04f730` | Autogenerada y leída: tablas de acceso, `movimiento_stock`, cambios de `cliente` y `libro` | B6, PR #76 en revisión |
| 4 | — | Escrita a mano: disparador de sólo agregado sobre `movimiento_stock` (RN-12) | E6, pendiente |

## Seed data inicial (`seed.py`, págs. 19-20)

`seed.py` vacía las tablas y carga como mínimo:
- **Usuarios:** los cinco de [03](03_actores_y_roles.md).
- **Catálogo:** 3 editoriales, 3 géneros y 6 autores del TP. Libros con stock: Rayuela 10, Antología de la literatura fantástica 5, Ficciones 8, Respiración artificial 3 y Bestiario 1.
- **Clientes:** Lucía Fernández (con perfil) y Tomás Ríos, sin usuario; Ana Paz, con el usuario `ana@example.com`.
- **Venta 1:** de Lucía, registrada por `vendedor@example.com`, con 1 Rayuela y 2 Ficciones, total 69000.00.
- **Movimientos:** un "Stock inicial" por libro (Rayuela 11 y Ficciones 10) y las dos salidas de la venta 1 (−1 y −2), de modo que se cumple el invariante en los cinco libros.
- **Historial de seguridad:** una línea con actor `SISTEMA`, "Carga de los datos iniciales".
