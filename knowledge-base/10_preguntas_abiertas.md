# Preguntas Abiertas

## Inconsistencias detectadas

### IN-01 — `main.py` y `seed.py` no están en la raíz *(Resuelta — DD-08)*
**Consigna (pág. 8):** `main.py` y `seed.py` van en la raíz del proyecto.
**Repo:** `app/main.py` y `scripts/seed.py`. Además, el Dockerfile del TP arranca `app.main:app` (pág. 14), pero eso es del despliegue, no del parcial.
**Impacto:** la estructura se corrige por estructura (6 % del puntaje, pág. 23), y los casos piden `python seed.py` (pág. 21).
**Resolución acordada (DD-08):** R8 lleva `seed.py` a la raíz. `main.py` se mantiene en `app/main.py` durante el desarrollo para no generar conflictos en las ramas abiertas y se mueve a `main.py` en la raíz al cierre, antes de entregar (con el checklist de [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md)). Queda definir quién ejecuta ese movimiento final y en qué tarea (por ejemplo en I1 o antes de E10).

### IN-02 — Dos archivos de paginación
**Consigna (págs. 8, 10):** `app/core/paginacion.py` con el envoltorio `{items, total, page, size, pages}`.
**Repo:** existe (B5), pero los routers siguen usando `app/core/pagination.py` (limit/offset del TP).
**Impacto:** los listados no cumplen el Ej. 3 hasta que cada módulo pase al envoltorio.
**Resolución propuesta:** que cada issue de módulo (E4, J6, J7, R6, R7) use `paginacion.py`, y borrar `pagination.py` cuando nadie lo importe.

### IN-03 — Numeración de reglas del TP viejo en el código
**Consigna (pág. 6):** las reglas se numeran de nuevo (RN-01 a RN-16).
**Repo:** los comentarios usan números del TP: "RN-10" para paginación, "RN-12" para errores, "RN-09" para el perfil, etc.
**Impacto:** confusión al revisar o al escribir specs.
**Resolución propuesta:** usar siempre la numeración del parcial en lo nuevo y corregir los comentarios cuando se toque cada archivo.

### IN-04 — `health` tiene `service.py`
**Consigna (pág. 9):** el módulo `health` sólo tiene `router.py`.
**Repo:** tiene `router.py` y `service.py`.
**Resolución propuesta:** lo revisa B2 (lifespan y health).

### IN-05 — El tablero no refleja lo mergeado
**Tablero:** H4 figura en *Todo*.
**Repo:** el PR #75 (`feat/h4-login`) está mergeado y su change `h4-auth-login` está archivado.
**Resolución propuesta:** que Hernán mueva H4 a *Done*. `CHANGES.md` usa el estado real de los PR.

### IN-06 — UoW y migración 3 todavía no están en `main`
**Repo:** `app/core/unit_of_work.py` (B4, PR #77) y la migración 3 (B6, PR #76) están en revisión.
**Impacto:** las tareas que los usan (H3, J3, R4, R5, E4…) tienen que esperar el merge o partir de esas ramas.

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|---|---|---|---|
| Alta | Fecha límite de entrega: se publica en el campus (pág. 24). Anotarla en el tablero. | Cierre | Grupo |
| Media | ¿Quién ejecuta el movimiento final de `app/main.py` a `main.py` en la raíz (DD-08) y en qué tarea (por ejemplo I1, la integración, o E10, el armado del zip)? | Cierre (I1 / E10) | Grupo |
| Media | ¿Quién borra `app/core/pagination.py` cuando todos los módulos usen el envoltorio? (IN-02) | Ej. 3 | Grupo |
| Media | ¿Puerto y URL del VPS asignados por la cátedra? (pág. 15) | E8, E9 | Cátedra |
| Baja | ¿Se corrigen los números de RN viejos en un change aparte o al tocar cada archivo? (IN-03) | — | Grupo |
