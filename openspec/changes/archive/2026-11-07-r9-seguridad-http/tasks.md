# Tasks: r9-seguridad-http

- [x] 1. Crear `test/seguridad.http` con los logins iniciales (`loginAdmin`, `loginVendedor`, `loginAna`, `loginNuevo`) y los casos C-06, C-07, C-08 y C-09 usando `# @name` y `# @no-cookie-jar`.
- [x] 2. Agregar un test de verificación en `tests/test_dos_grupos_rutas.py` (o ejecutar la suite completa de `unittest`) que compruebe la existencia y estructura de `test/seguridad.http`.
- [x] 3. Ejecutar `python -m unittest discover -s tests` y archivar el change con `openspec archive "r9-seguridad-http" -y`.
