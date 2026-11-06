import sys
import unittest
from pydantic import ValidationError

sys.path.insert(
    0,
    r"C:\Users\Dell\Documents\Semestre 3\Programacion 3\tp_objeto_a_Persistencia\Librer-a_Prog.3_2026",
)


class TestAuthLoginSchemas(unittest.TestCase):
    def test_01_login_request_valid(self):
        from app.modules.usuarios.schemas import LoginRequest

        req = LoginRequest(email="ana@example.com", password="Password123!")
        self.assertEqual(req.email, "ana@example.com")
        self.assertEqual(req.password, "Password123!")

    def test_02_login_request_extra_fields_forbidden(self):
        from app.modules.usuarios.schemas import LoginRequest

        with self.assertRaises(ValidationError):
            LoginRequest(email="ana@example.com", password="Password123!", rol="ADMIN")

    def test_03_login_request_password_max_72_bytes(self):
        from app.modules.usuarios.schemas import LoginRequest

        # 72 bytes OK
        ok_req = LoginRequest(email="ana@example.com", password="a" * 72)
        self.assertEqual(len(ok_req.password.encode("utf-8")), 72)

        # 73 bytes raises ValidationError (422)
        with self.assertRaises(ValidationError):
            LoginRequest(email="ana@example.com", password="a" * 73)

        # 36 'ñ' (72 bytes) OK
        ok_utf8 = LoginRequest(email="ana@example.com", password="ñ" * 36)
        self.assertEqual(len(ok_utf8.password.encode("utf-8")), 72)

        # 36 'ñ' + 'a' (73 bytes) raises ValidationError (422)
        with self.assertRaises(ValidationError):
            LoginRequest(email="ana@example.com", password=("ñ" * 36) + "a")

    def test_04_login_response_structure(self):
        from app.modules.usuarios.schemas import LoginResponse

        resp = LoginResponse(
            debe_cambiar_password=False,
            expira_en_segundos=1800,
        )
        self.assertEqual(resp.mensaje, "Sesión iniciada")
        self.assertFalse(resp.debe_cambiar_password)
        self.assertEqual(resp.expira_en_segundos, 1800)

    def test_05_auth_domain_exceptions(self):
        from app.modules.usuarios.schemas import (
            CredencialesInvalidasError,
            LimiteIntentosError,
        )

        err_cred = CredencialesInvalidasError("Credenciales inválidas")
        self.assertIn("Credenciales", str(err_cred))

        err_limite = LimiteIntentosError(retry_after=42)
        self.assertEqual(err_limite.retry_after, 42)
        self.assertIn("Demasiados intentos", str(err_limite))


if __name__ == "__main__":
    unittest.main()
