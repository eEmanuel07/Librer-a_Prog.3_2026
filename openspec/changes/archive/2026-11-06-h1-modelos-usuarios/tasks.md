# Tasks: h1-modelos-usuarios

- [x] 1.1 Definir el modelo `Usuario` con columnas `id`, `email` único, `password_hash`, `activo`, `debe_cambiar_password` y relaciones con `lazy='raise'`.
  _Evidencia: `test_h1_models.py::test_01_import_usuarios_models_and_table_names` y `test_02_usuario_columns_and_constraints` pasando OK._
- [x] 1.2 Definir el modelo `AsignacionRol` con check de roles, índices de FKs y el índice único parcial `uq_asignacion_rol_vigente` sobre `(usuario_id, rol) WHERE revocada_en IS NULL`.
  _Evidencia: `test_h1_models.py::test_03_asignacion_rol_columns_fks_checks_and_partial_index` pasando OK._
- [x] 1.3 Definir los modelos `IntentoAcceso` (con índice compuesto email/ip/cuando) y `EventoSeguridad` (actor de texto).
  _Evidencia: `test_h1_models.py::test_04_intento_acceso_and_evento_seguridad` pasando OK._
- [x] 1.4 Extender `Cliente` con `usuario_id` único/nulo y relación 1 a 1 `uselist=False` hacia `Usuario`.
  _Evidencia: `test_h1_models.py::test_05_cliente_usuario_id_and_full_mapper_configuration_with_e1` pasando OK._
- [x] 1.5 Verificar que la configuración de mappers de SQLAlchemy cargue sin ambigüedades (`configure_mappers()`).
  _Evidencia: Suite `test_h1_models.py` 5/5 tests pasando OK sin `AmbiguousForeignKeysError`._
