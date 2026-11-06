import unittest
from pydantic import ValidationError

from app.modules.usuarios.schemas import (
    CambioPasswordRequest,
    MensajeResponse,
    YoResponse,
)


class TestAuthLogoutYoCambioSchemas(unittest.TestCase):
    def test_01_mensaje_response_estructura(self):
        resp = MensajeResponse(mensaje="Operación exitosa")
        self.assertEqual(resp.mensaje, "Operación exitosa")

    def test_02_yo_response_estructura(self):
        resp = YoResponse(
            id=10,
            email="admin@example.com",
            nombre="Administrador",
            debe_cambiar_password=False,
            roles=["ADMIN"],
            roles_token=["ADMIN"],
        )
        self.assertEqual(resp.id, 10)
        self.assertEqual(resp.email, "admin@example.com")
        self.assertEqual(resp.nombre, "Administrador")
        self.assertFalse(resp.debe_cambiar_password)
        self.assertEqual(resp.roles, ["ADMIN"])
        self.assertEqual(resp.roles_token, ["ADMIN"])

    def test_03_cambio_password_request_valido(self):
        req = CambioPasswordRequest(
            password_actual="ClaveVieja123!",
            password_nueva="ClaveNueva456!",
        )
        self.assertEqual(req.password_actual, "ClaveVieja123!")
        self.assertEqual(req.password_nueva, "ClaveNueva456!")

    def test_04_cambio_password_request_campos_extra_prohibidos(self):
        with self.assertRaises(ValidationError) as ctx:
            CambioPasswordRequest(
                password_actual="ClaveVieja123!",
                password_nueva="ClaveNueva456!",
                campo_extra="no_permitido",
            )
        self.assertTrue(any(e["type"] == "extra_forbidden" for e in ctx.exception.errors()))

    def test_05_cambio_password_request_rechaza_password_actual_mas_de_72_bytes(self):
        with self.assertRaises(ValidationError):
            CambioPasswordRequest(
                password_actual="a" * 73,
                password_nueva="Valida123!",
            )

    def test_06_cambio_password_request_rechaza_password_nueva_mas_de_72_bytes(self):
        with self.assertRaises(ValidationError):
            CambioPasswordRequest(
                password_actual="Valida123!",
                password_nueva="b" * 73,
            )

    def test_07_cambio_password_request_rechaza_password_vacia(self):
        with self.assertRaises(ValidationError):
            CambioPasswordRequest(
                password_actual="",
                password_nueva="Valida123!",
            )
        with self.assertRaises(ValidationError):
            CambioPasswordRequest(
                password_actual="Valida123!",
                password_nueva="",
            )


if __name__ == "__main__":
    unittest.main()
