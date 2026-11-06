import unittest
from pydantic import ValidationError

from app.modules.usuarios.schemas import RegistroRequest, RegistroResponse


class TestAuthRegistroSchemas(unittest.TestCase):
    def test_01_registro_request_valido_normaliza_email(self):
        req = RegistroRequest(
            nombre="  Carlos Gardel  ",
            email="  Carlos.GARDEL@Example.COM  ",
            password="MiPassword123!",
        )
        self.assertEqual(req.nombre, "Carlos Gardel")
        self.assertEqual(req.email, "carlos.gardel@example.com")
        self.assertEqual(req.password, "MiPassword123!")

    def test_02_registro_request_campos_extra_prohibidos(self):
        with self.assertRaises(ValidationError) as ctx:
            RegistroRequest(
                nombre="Hacker",
                email="hacker@example.com",
                password="Password123!",
                rol="ADMIN",  # Campo extra prohibido
            )
        errores = ctx.exception.errors()
        self.assertTrue(any(e["type"] == "extra_forbidden" for e in errores))

    def test_03_registro_request_password_maximo_72_bytes(self):
        # 73 caracteres ASCII = 73 bytes
        password_larga = "A" * 73
        with self.assertRaises(ValidationError):
            RegistroRequest(
                nombre="Test",
                email="test@example.com",
                password=password_larga,
            )

        # 36 caracteres 'ñ' = 72 bytes en UTF-8 (válido)
        password_72_bytes = "ñ" * 36
        req = RegistroRequest(
            nombre="Test",
            email="test@example.com",
            password=password_72_bytes,
        )
        self.assertEqual(req.password, password_72_bytes)

    def test_04_registro_request_nombre_no_vacio(self):
        with self.assertRaises(ValidationError):
            RegistroRequest(
                nombre="   ",
                email="test@example.com",
                password="Password123!",
            )

    def test_05_registro_response_estructura(self):
        resp = RegistroResponse(
            id=10,
            email="nuevo@example.com",
            nombre="Nuevo Usuario",
            cliente_id=25,
        )
        self.assertEqual(resp.id, 10)
        self.assertEqual(resp.email, "nuevo@example.com")
        self.assertEqual(resp.nombre, "Nuevo Usuario")
        self.assertEqual(resp.cliente_id, 25)
        self.assertEqual(resp.mensaje, "Usuario registrado exitosamente")
        self.assertNotIn("password_hash", resp.model_dump())


if __name__ == "__main__":
    unittest.main()
