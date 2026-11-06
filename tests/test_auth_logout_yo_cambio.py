import unittest
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
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
from app.core.dependencies import get_usuario_actual
from app.core.security import crear_access_token, hashear_password, verificar_password
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
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
        self._s.flush()

    async def commit(self):
        self._s.commit()

    async def rollback(self):
        self._s.rollback()

    async def exec(self, statement):
        return self._s.exec(statement)

    async def get(self, entity_class, ident):
        return self._s.get(entity_class, ident)


class TestAuthLogoutYoCambioEndpoints(unittest.IsolatedAsyncioTestCase):
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

        async def override_get_session():
            with Session(self.engine, expire_on_commit=False) as s:
                yield _AsyncSessionAdapter(s)

        async def override_get_uow(session=Depends(override_get_session)):
            yield UsuarioUnitOfWork(session)

        self.app.dependency_overrides[get_session] = override_get_session
        self.app.dependency_overrides[get_usuario_uow] = override_get_uow
        self.app.dependency_overrides[get_settings] = lambda: self.settings

        self.client = TestClient(self.app)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_logout_elimina_cookie_de_sesion_idempotente(self):
        # Con cookie previa
        resp = self.client.post("/auth/logout", cookies={"access_token": "un-token-cualquiera"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"mensaje": "Sesión cerrada"})
        set_cookie = resp.headers.get("set-cookie", "").lower()
        self.assertIn("access_token", set_cookie)
        self.assertIn("max-age=0", set_cookie)

        # Sin cookie previa (idempotente)
        resp2 = self.client.post("/auth/logout")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json(), {"mensaje": "Sesión cerrada"})

    async def test_02_yo_autenticado_retorna_perfil_y_roles(self):
        with Session(self.engine) as s:
            u = Usuario(
                id=1,
                nombre="Lucía Gómez",
                email="lucia@example.com",
                password_hash="fakehash",
                activo=True,
                debe_cambiar_password=True,
            )
            s.add(u)
            s.commit()
            s.add(AsignacionRol(usuario_id=1, rol="ADMIN"))
            s.commit()

        token = crear_access_token(1, ["ADMIN", "VENDEDOR"], settings=self.settings)

        resp = self.client.get("/auth/yo", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["email"], "lucia@example.com")
        self.assertEqual(data["nombre"], "Lucía Gómez")
        self.assertTrue(data["debe_cambiar_password"])
        self.assertEqual(data["roles"], ["ADMIN"])
        self.assertEqual(data["roles_token"], ["ADMIN", "VENDEDOR"])

    async def test_03_yo_sin_sesion_retorna_401(self):
        resp = self.client.get("/auth/yo")
        self.assertEqual(resp.status_code, 401)

    async def test_04_cambiar_password_exitoso_no_invalida_sesion_y_crea_evento(self):
        hash_inicial = await hashear_password("PasswordActual123!", settings=self.settings)
        with Session(self.engine) as s:
            u = Usuario(
                id=2,
                nombre="Pedro",
                email="pedro@example.com",
                password_hash=hash_inicial,
                activo=True,
                debe_cambiar_password=True,
            )
            s.add(u)
            s.commit()

        token = crear_access_token(2, ["CLIENTE"], settings=self.settings)

        payload = {
            "password_actual": "PasswordActual123!",
            "password_nueva": "PasswordNueva456!",
        }

        resp = self.client.post("/auth/cambiar-password", json=payload, cookies={"access_token": token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"mensaje": "Contraseña actualizada exitosamente"})

        # En la BD la clave nueva funciona y se registró EventoSeguridad (RN-16)
        with Session(self.engine) as s:
            user = s.get(Usuario, 2)
            self.assertFalse(user.debe_cambiar_password)
            self.assertTrue(await verificar_password("PasswordNueva456!", user.password_hash, settings=self.settings))

            eventos = s.exec(select(EventoSeguridad).where(EventoSeguridad.actor == "pedro@example.com")).all()
            self.assertEqual(len(eventos), 1)
            self.assertEqual(eventos[0].accion, "Cambio de contraseña")

    async def test_05_cambiar_password_clave_actual_incorrecta_retorna_401(self):
        hash_inicial = await hashear_password("PasswordCorrecta123!", settings=self.settings)
        with Session(self.engine) as s:
            u = Usuario(
                id=3,
                nombre="Ana",
                email="ana@example.com",
                password_hash=hash_inicial,
                activo=True,
            )
            s.add(u)
            s.commit()

        token = crear_access_token(3, ["CLIENTE"], settings=self.settings)

        payload = {
            "password_actual": "PasswordErronea123!",
            "password_nueva": "PasswordNueva456!",
        }

        resp = self.client.post("/auth/cambiar-password", json=payload, cookies={"access_token": token})
        self.assertEqual(resp.status_code, 401)

    async def test_06_cambiar_password_mas_de_72_bytes_retorna_422(self):
        with Session(self.engine) as s:
            u = Usuario(
                id=4,
                nombre="Test422",
                email="test422@example.com",
                password_hash="fakehash",
                activo=True,
            )
            s.add(u)
            s.commit()

        token = crear_access_token(4, ["CLIENTE"], settings=self.settings)

        payload = {
            "password_actual": "Valida123!",
            "password_nueva": "a" * 73,
        }

        resp = self.client.post("/auth/cambiar-password", json=payload, cookies={"access_token": token})
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
