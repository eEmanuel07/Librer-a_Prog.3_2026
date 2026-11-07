"""Tests de alta de personal con contraseña provisoria (issue #48, [R4])."""

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.modules.autores.models  # noqa: F401
import app.modules.clientes.models  # noqa: F401
import app.modules.editoriales.models  # noqa: F401
import app.modules.generos.models  # noqa: F401
import app.modules.libros.models  # noqa: F401
import app.modules.ventas.models  # noqa: F401
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import crear_access_token, verificar_password
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from app.modules.usuarios.router import router as auth_router
from app.modules.usuarios.router import router_usuarios


def _make_settings(**overrides) -> Settings:
    defaults = {
        "postgres_password": "secret-db-password",
        "jwt_secret": "a" * 32,
        "jwt_expira_minutos": 30,
        "cookie_secure": False,
        "bcrypt_costo": 4,
        "bcrypt_concurrencia": 2,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class _AsyncSessionAdapter:
    def __init__(self, sync_session: Session) -> None:
        self._s = sync_session

    def add(self, obj):
        self._s.add(obj)

    async def flush(self):
        self._s.flush()

    async def commit(self):
        self._s.commit()

    async def rollback(self):
        self._s.rollback()

    async def exec(self, statement):
        return self._s.exec(statement)

    async def get(self, entity_class, ident):
        return self._s.get(entity_class, ident)


class TestAltaPersonal(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _make_settings()

        self.app = FastAPI()
        self.app.include_router(auth_router)
        self.app.include_router(router_usuarios)

        async def override_get_session():
            with Session(self.engine, expire_on_commit=False) as s:
                yield _AsyncSessionAdapter(s)

        self.app.dependency_overrides[get_session] = override_get_session
        self.app.dependency_overrides[get_settings] = lambda: self.settings

        self.client = TestClient(self.app)

        with Session(self.engine) as s:
            admin = Usuario(
                id=1,
                email="admin@example.com",
                nombre="Admin Uno",
                password_hash="hash",
                activo=True,
            )
            vendedor = Usuario(
                id=2,
                email="vendedor@example.com",
                nombre="Vendedor",
                password_hash="hash",
                activo=True,
            )
            s.add_all([admin, vendedor])
            s.commit()
            s.add_all(
                [
                    AsignacionRol(usuario_id=1, rol="ADMIN"),
                    AsignacionRol(usuario_id=2, rol="VENDEDOR"),
                ]
            )
            s.commit()

        self.token_admin = crear_access_token(1, ["ADMIN"], settings=self.settings)
        self.token_vendedor = crear_access_token(2, ["VENDEDOR"], settings=self.settings)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_admin_crea_personal_con_debe_cambiar_password_y_evento(self):
        resp = self.client.post(
            "/usuarios",
            json={
                "nombre": "Nuevo Empleado",
                "email": "Nuevo@Example.com",
                "password": "Provisoria123!",
            },
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(resp.status_code, 201)
        datos = resp.json()
        self.assertEqual(datos["email"], "nuevo@example.com")
        self.assertEqual(datos["nombre"], "Nuevo Empleado")
        self.assertTrue(datos["activo"])
        self.assertTrue(datos["debe_cambiar_password"])
        self.assertNotIn("password_hash", datos)
        self.assertNotIn("password", datos)

        with Session(self.engine) as s:
            creado = s.get(Usuario, datos["id"])
            self.assertIsNotNone(creado)
            self.assertTrue(creado.debe_cambiar_password)
            self.assertTrue(
                await verificar_password(
                    "Provisoria123!", creado.password_hash, settings=self.settings
                )
            )
            eventos = s.exec(select(EventoSeguridad)).all()
            self.assertEqual(len(eventos), 1)
            self.assertEqual(eventos[0].actor, "admin@example.com")
            self.assertIn("nuevo@example.com", eventos[0].accion)

    async def test_02_correo_duplicado_da_409_y_no_deja_evento_seguridad(self):
        resp = self.client.post(
            "/usuarios",
            json={
                "nombre": "Repetido",
                "email": "vendedor@example.com",
                "password": "Provisoria123!",
            },
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(resp.status_code, 409)

        with Session(self.engine) as s:
            eventos = s.exec(select(EventoSeguridad)).all()
            self.assertEqual(len(eventos), 0)

    async def test_03_validaciones_de_contrato_72_bytes_y_extra_forbid_dan_422(self):
        resp_72 = self.client.post(
            "/usuarios",
            json={
                "nombre": "Largo",
                "email": "largo@example.com",
                "password": "a" * 73,
            },
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(resp_72.status_code, 422)

        resp_extra = self.client.post(
            "/usuarios",
            json={
                "nombre": "Extra",
                "email": "extra@example.com",
                "password": "Provisoria123!",
                "rol": "ADMIN",
            },
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(resp_extra.status_code, 422)

    async def test_04_vendedor_no_puede_crear_personal_da_403_y_sin_sesion_da_401(self):
        resp_403 = self.client.post(
            "/usuarios",
            json={
                "nombre": "Intento",
                "email": "intento@example.com",
                "password": "Provisoria123!",
            },
            cookies={"access_token": self.token_vendedor},
        )
        self.assertEqual(resp_403.status_code, 403)

        resp_401 = self.client.post(
            "/usuarios",
            json={
                "nombre": "Intento",
                "email": "intento@example.com",
                "password": "Provisoria123!",
            },
        )
        self.assertEqual(resp_401.status_code, 401)


if __name__ == "__main__":
    unittest.main()
