# Tasks: h7-auth-http

## 1. Casos de Entrada y Registro (C-01 y C-02)

- [ ] 1.1 Configurar variables base y redactar caso C-01 (parámetro inválido / contrato estricto devolviendo 422 sin 500) en `test/auth.http`
- [ ] 1.2 Redactar caso C-02 (auto-registro exitoso con 201 y duplicado con 409 sin apropiación de ficha) en `test/auth.http`

## 2. Casos de Login, Anti-Enumeración y Rate Limit (C-03, C-04 y C-05)

- [ ] 2.1 Redactar caso C-03 (login con credenciales válidas emitiendo cookie HttpOnly y respuesta 200 sin token en body) en `test/auth.http`
- [ ] 2.2 Redactar caso C-04 (mismo 401 y tiempo equivalente ante contraseña incorrecta o correo inexistente) en `test/auth.http`
- [ ] 2.3 Redactar caso C-05 (secuencia de 5 fallos consecutivos y 6to intento devolviendo 429 con cabecera `Retry-After: 60`) en `test/auth.http`

## 3. Flujo de Sesión, Auditoría y Verificación

- [ ] 3.1 Redactar peticiones complementarias para `GET /auth/yo`, `POST /auth/cambiar-password` y `POST /auth/logout` en `test/auth.http`
- [ ] 3.2 Verificar la coherencia del archivo `test/auth.http` y validar el change con `openspec validate --all --strict`

## Workflow follow-up

- Implementar el archivo `test/auth.http` según las tareas desglosadas.
- Validar y archivar el change con `openspec archive h7-auth-http`.
