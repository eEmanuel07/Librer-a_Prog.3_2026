# Tasks: r7-proteger-catalogo

- [x] 1. Escribir tests en `tests/test_catalogo_protegido.py` verificando C-06 (401 sin sesión, 403 para VENDEDOR, 201/200 para ADMIN), envoltorio `Pagina` en los listados de editoriales, géneros y autores, 422 en página fuera de rango, 409 por unicidad, y exclusión de libros dados de baja.
- [x] 2. Actualizar `repository.py`, `service.py` y `router.py` de `app/modules/editoriales/`.
- [x] 3. Actualizar `repository.py`, `service.py` y `router.py` de `app/modules/generos/`.
- [x] 4. Actualizar `repository.py`, `service.py` y `router.py` de `app/modules/autores/`.
- [x] 5. Ejecutar la suite completa de tests con `python -m unittest discover -s tests`.
