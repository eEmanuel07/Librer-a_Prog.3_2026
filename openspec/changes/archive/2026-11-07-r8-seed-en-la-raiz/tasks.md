# Tasks: r8-seed-en-la-raiz

- [x] 1. Escribir `tests/test_seed.py` verificando que `sembrar()` carga usuarios, roles, catálogo, clientes, venta 1, movimientos con invariante cumplido (`ids_con_stock_inconsistente() == []`) y el evento `SISTEMA`, además de ser idempotente al correrlo más de una vez.
- [x] 2. Crear `seed.py` en la raíz del repositorio e implementar `sembrar()` y `CONTRASENAS_PRUEBA`.
- [x] 3. Eliminar `scripts/seed.py` y `scripts/__init__.py`.
- [x] 4. Ejecutar la suite completa con `python -m unittest discover -s tests`.
