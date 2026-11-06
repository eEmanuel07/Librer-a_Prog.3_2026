# Tasks: h5-intento-acceso-sesion-propia

- [x] 1.1 Implementar `IntentoAccesoRepository` en `app/modules/usuarios/repository.py` con `contar_fallos_vigentes_y_primer_fallo` en una sola consulta con `scalar_subquery`.
  _Evidencia: `test_h5_intento_acceso.py::test_01_repository_contract_and_single_query_with_scalar_subquery` pasando OK._
- [x] 1.2 Implementar `registrar_intento_acceso` en `app/modules/usuarios/unit_of_work.py` con sesión propia, commit y comentario obligatorio de 3 partes.
  _Evidencia: `test_h5_intento_acceso.py::test_02_registrar_intento_acceso_default_utc_and_mandatory_comment` pasando OK._
- [x] 1.3 Verificar que 5 intentos fallidos sobrevivan al rollback de la transacción de la petición.
  _Evidencia: `test_h5_intento_acceso.py::test_03_five_failed_attempts_survive_request_rollback_and_single_query_count` pasando OK._
- [x] 1.4 Verificar que un login exitoso posterior reinicie el conteo manteniendo el historial.
  _Evidencia: `test_h5_intento_acceso.py::test_04_successful_login_resets_count_while_keeping_history` pasando OK._
