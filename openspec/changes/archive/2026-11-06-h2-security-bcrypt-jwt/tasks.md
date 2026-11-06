# Tasks: h2-security-bcrypt-jwt

- [x] 1.1 Implementar tipo y validador `PasswordBcrypt` restringiendo contraseñas a 1-72 bytes UTF-8.
  _Evidencia: `test_h2_security.py::test_01_password_72_bytes_contract_validation` y `test_05_fastapi_endpoint_returns_422_on_73_bytes` pasando OK._
- [x] 1.2 Implementar `hashear_password` y `verificar_password` fuera del bucle de eventos (`asyncio.to_thread`) y bajo semáforo asincrónico por loop.
  _Evidencia: `test_h2_security.py::test_02_hashear_and_verificar_password_with_to_thread_and_semaphore` pasando OK._
- [x] 1.3 Verificar que el semáforo limite la concurrencia máxima declarada en `Settings.bcrypt_concurrencia`.
  _Evidencia: `test_h2_security.py::test_03_semaphore_limits_concurrent_bcrypt_calls` pasando OK._
- [x] 1.4 Implementar `crear_access_token` y `decodificar_access_token` con claims `sub`, `exp`, `roles`, control de vencimiento y firma.
  _Evidencia: `test_h2_security.py::test_04_jwt_encode_and_decode_valid_expired_and_invalid` pasando OK._
- [x] 1.5 Implementar `calcular_hash_ficticio` para el ciclo de vida del login.
  _Evidencia: Verificado con `calcular_hash_ficticio(settings)` produciendo hash válido con costo configurado._
