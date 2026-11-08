# Design: e7-http-libros

## Context

`seed.py` deja siempre los mismos datos (el `TRUNCATE ... RESTART IDENTITY` reinicia los ids): los libros 1 a 5 son Rayuela (stock 10), Ficciones (8), Bestiario (1), Respiración artificial (3) y la Antología (5), y la venta 1 de Lucía tiene 1 Rayuela y 2 Ficciones. `test/seguridad.http` (R9) ya fijó cómo se mantienen varias sesiones a la vez en un `.http`.

## Decisions

### 1. Ids fijos para los datos del seed, variables de respuesta para lo nuevo

Lo que carga el seed se pide por id (`/libros/1`, `/ventas/1`), porque es reproducible. Lo que crea el archivo se toma de la respuesta (`{{rayuelaNueva.response.body.$.id}}`): un alta rechazada también consume un valor de la secuencia en PostgreSQL, así que el id siguiente no se puede adivinar.

### 2. C-16 antes que C-13

C-13 da de baja Rayuela. Si fuera primero, el listado y las búsquedas de C-16 contarían un libro menos. C-16 usa Ficciones y Bestiario, que C-13 no da de baja.

### 3. El libro que se da de baja en C-13 es Rayuela

Rayuela está en la venta 1. Darla de baja permite mostrar, en el mismo archivo, que la venta vieja sigue mostrando su título (RN-13), y su ISBN es el que se vuelve a cargar.

### 4. Misma convención de sesiones que `seguridad.http`

Cada login tiene `# @name` y cada pedido con sesión usa `# @no-cookie-jar` y `Cookie: {{loginX.response.headers.Set-Cookie}}`. Así se ven en el mismo archivo el 403 del VENDEDOR y el 201 del ADMIN sin cerrar sesión, y el archivo se lee igual que el de seguridad.

### 5. Comprobación automática antes de subirlo

No hay un cliente `.http` en `requirements.txt`. Antes del PR se corre el archivo con un script descartable que lo lee pedido por pedido y compara el código de cada respuesta con su `# Esperado:`, contra una base temporal de PostgreSQL con `alembic upgrade head` y `python seed.py`.

## Risks / Trade-offs

- **[Riesgo] El archivo cambia los datos** (repone, da de baja, carga un libro) → hay que correr `python seed.py` antes de cada pasada, como pide la consigna para todos los `.http`. Queda escrito al principio del archivo.
