import unittest
from contextlib import asynccontextmanager

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
from app.core.security import verificar_password
from app.modules.clientes.models import Cliente
from app.modules.usuarios.models import AsignacionRol, Usuario
from app.modules.usuarios.router import router as auth_router
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork, get_usuario_uow


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
        try:
            self._s.flush()
        except Exception as exc:
            if hasattr(exc, "orig") and exc.orig is not None and not hasattr(exc.orig, "sqlstate"):
                setattr(exc.orig, "sqlstate", "23505")
            raise

    async def commit(self):
        try:
            self._s.commit()
        except Exception as exc:
            if hasattr(exc, "orig") and exc.orig is not None and not hasattr(exc.orig, "sqlstate"):
                setattr(exc.orig, "sqlstate", "23505")
            raise

    async def rollback(self):
        self._s.rollback()

    async def exec(self, statement):
        return self._s.exec(statement)

    async def get(self, entity_class, ident):
        return self._s.get(entity_class, ident)


class TestAuthRegistroEndpoint(unittest.IsolatedAsyncioTestCase):
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

        @asynccontextmanager
        async def factory():
            with Session(self.engine, expire_on_commit=False) as s:
                yield _AsyncSessionAdapter(s)

        self.app.state.session_factory = factory
        self.app.state.settings = self.settings

        async def override_get_uow():
            with Session(self.engine, expire_on_commit=False) as s:
                yield UsuarioUnitOfWork(_AsyncSessionAdapter(s))

        self.app.dependency_overrides[get_usuario_uow] = override_get_uow
        self.app.dependency_overrides[get_settings] = lambda: self.settings

        self.client = TestClient(self.app)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_registro_exitoso_crea_las_tres_entidades_y_responde_201(self):
        payload = {
            "nombre": "Ana Gómez",
            "email": "ana.gomez@example.com",
            "password": "Password123!",
        }

        resp = self.client.post("/auth/registro", json=payload)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()

        self.assertIn("id", data)
        self.assertIn("cliente_id", data)
        self.assertEqual(data["email"], "ana.gomez@example.com")
        self.assertEqual(data["nombre"], "Ana Gómez")
        self.assertEqual(data["mensaje"], "Usuario registrado exitosamente")
        self.assertNotIn("password_hash", data)
        self.assertNotIn("password", data)

        # Cookie no exigida en registro
        self.assertNotIn("access_token", resp.cookies)

        # Verificar en base de datos las 3 filas
        with Session(self.engine) as s:
            user = s.exec(select(Usuario).where(Usuario.email == "ana.gomez@example.com")).first()
            self.assertIsNotNone(user)
            self.assertTrue(user.activo)
            self.assertFalse(user.debe_cambiar_password)
            self.assertTrue(await verificar_password("Password123!", user.password_hash, settings=self.settings))

            asig = s.exec(select(AsignacionRol).where(AsignacionRol.usuario_id == user.id)).first()
            self.assertIsNotNone(asig)
            self.assertEqual(asig.rol, "CLIENTE")

            cli = s.exec(select(Cliente).where(Cliente.email == "ana.gomez@example.com")).first()
            self.assertIsNotNone(cli)
            self.assertEqual(cli.usuario_id, user.id)
            self.assertEqual(cli.nombre, "Ana Gómez")

    async def test_02_caso_c02_cliente_preexistente_da_409_y_no_se_apropia_de_ficha(self):
        # Insertar cliente de mostrador preexistente sin usuario
        with Session(self.engine) as s:
            cliente_existente = Cliente(
                nombre="Mostrador Cliente",
                email="mostrador@example.com",
                usuario_id=None,
            )
            s.add(cliente_existente)
            s.commit()
            s.refresh(cliente_existente)
            original_cliente_id = cliente_existente.id

        payload = {
            "nombre": "Nuevo Intruso",
            "email": "mostrador@example.com",
            "password": "Password123!",
        }

        resp = self.client.post("/auth/registro", json=payload)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["detail"], "El correo electrónico ya está registrado")

        # Comprobar que el cliente existente sigue intacto con usuario_id en None
        # y que no se crearon usuarios ni roles huérfanos
        with Session(self.engine) as s:
            cli = s.exec(select(Cliente).where(Cliente.id == original_cliente_id)).first()
            self.assertIsNotNone(cli)
            self.assertIsNone(cli.usuario_id)
            self.assertEqual(cli.nombre, "Mostrador Cliente")

            u = s.exec(select(Usuario).where(Usuario.email == "mostrador@example.com")).first()
            self.assertIsNone(u)

            asigs = s.exec(select(AsignacionRol)).all()
            self.assertEqual(len(asigs), 0)

    async def test_03_correo_duplicado_en_usuario_da_409_y_no_deja_filas_huerfanas(self):
        # Insertar usuario previo
        with Session(self.engine) as s:
            u = Usuario(
                nombre="Usuario Existente",
                email="yaexiste@example.com",
                password_hash="fakehash",
                activo=True,
            )
            s.add(u)
            s.commit()

        payload = {
            "nombre": "Otro",
            "email": "yaexiste@example.com",
            "password": "Password123!",
        }

        resp = self.client.post("/auth/registro", json=payload)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["detail"], "El correo electrónico ya está registrado")

        # Comprobar que no se creó cliente ni rol
        with Session(self.engine) as s:
            cli = s.exec(select(Cliente).where(Cliente.email == "yaexiste@example.com")).first()
            self.assertIsNone(cli)

    async def test_04_rechazo_campos_adicionales_422(self):
        payload = {
            "nombre": "Hacker",
            "email": "hacker@example.com",
            "password": "Password123!",
            "rol": "ADMIN",
        }

        resp = self.client.post("/auth/registro", json=payload)
        self.assertEqual(resp.status_code, 422)

    async def test_05_rechazo_password_excede_72_bytes_422(self):
        payload = {
            "nombre": "Test",
            "email": "test@example.com",
            "password": "a" * 73,
        }

        resp = self.client.post("/auth/registro", json=payload)
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
