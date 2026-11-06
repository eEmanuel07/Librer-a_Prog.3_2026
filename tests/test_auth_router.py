import sys
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

sys.path.insert(
    0,
    r"C:\Users\Dell\Documents\Semestre 3\Programacion 3\tp_objeto_a_Persistencia\Librer-a_Prog.3_2026",
)

import app.modules.autores.models  # noqa: F401
import app.modules.clientes.models  # noqa: F401
import app.modules.editoriales.models  # noqa: F401
import app.modules.generos.models  # noqa: F401
import app.modules.libros.models  # noqa: F401
import app.modules.ventas.models  # noqa: F401
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import calcular_hash_ficticio, hashear_password
from app.modules.usuarios.models import AsignacionRol, IntentoAcceso, Usuario
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


class TestAuthRouter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _make_settings()
        self.hash_ficticio = await calcular_hash_ficticio(self.settings)

        # Setup Test App
        from contextlib import asynccontextmanager

        from app.modules.usuarios.router import router as auth_router

        self.app = FastAPI()
        self.app.include_router(auth_router)

        @asynccontextmanager
        async def factory():
            with Session(self.engine, expire_on_commit=False) as s:
                yield _AsyncSessionAdapter(s)

        self.app.state.session_factory = factory
        self.app.state.settings = self.settings
        self.app.state.hash_ficticio = self.hash_ficticio

        async def override_get_uow():
            with Session(self.engine, expire_on_commit=False) as s:
                yield UsuarioUnitOfWork(_AsyncSessionAdapter(s))

        self.app.dependency_overrides[get_usuario_uow] = override_get_uow
        self.app.dependency_overrides[get_settings] = lambda: self.settings

        self.client = TestClient(self.app)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_c03_login_cookie_present_and_body_without_token(self):
        hashed = await hashear_password("Secreto123!", self.settings)
        with Session(self.engine) as s:
            u = Usuario(
                email="admin@example.com",
                nombre="Admin",
                password_hash=hashed,
                activo=True,
                debe_cambiar_password=False,
            )
            s.add(u)
            s.commit()
            s.refresh(u)
            s.add(AsignacionRol(usuario_id=u.id, rol="ADMIN"))
            s.commit()

        resp = self.client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "Secreto123!"},
        )
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["mensaje"], "Sesión iniciada")
        self.assertFalse(data["debe_cambiar_password"])
        self.assertEqual(data["expira_en_segundos"], 1800)
        self.assertNotIn("token", data)
        self.assertNotIn("access_token", data)

        # Cookie en Set-Cookie
        self.assertIn("access_token", resp.cookies)
        cookie = resp.cookies.get("access_token")
        self.assertTrue(len(cookie) > 20)

    async def test_02_c04_bad_password_and_nonexistent_email_return_same_401(self):
        hashed = await hashear_password("Secreto123!", self.settings)
        with Session(self.engine) as s:
            u = Usuario(
                email="ana@example.com",
                nombre="Ana",
                password_hash=hashed,
                activo=True,
            )
            s.add(u)
            s.commit()

        # Contraseña mala
        resp_bad_pw = self.client.post(
            "/auth/login",
            json={"email": "ana@example.com", "password": "ClaveIncorrecta"},
        )
        self.assertEqual(resp_bad_pw.status_code, 401)
        self.assertEqual(resp_bad_pw.json(), {"detail": "Credenciales inválidas"})

        # Correo inexistente
        resp_no_user = self.client.post(
            "/auth/login",
            json={"email": "noexiste@example.com", "password": "ClaveIncorrecta"},
        )
        self.assertEqual(resp_no_user.status_code, 401)
        self.assertEqual(resp_no_user.json(), {"detail": "Credenciales inválidas"})

    async def test_03_c05_sixth_attempt_returns_429_with_retry_after(self):
        # 5 intentos fallidos
        for _ in range(5):
            r = self.client.post(
                "/auth/login",
                json={"email": "bloqueado@example.com", "password": "Mala"},
            )
            self.assertEqual(r.status_code, 401)

        # 6to intento -> 429
        r6 = self.client.post(
            "/auth/login",
            json={"email": "bloqueado@example.com", "password": "Mala"},
        )
        self.assertEqual(r6.status_code, 429)
        self.assertIn("Retry-After", r6.headers)
        retry_val = int(r6.headers["Retry-After"])
        self.assertTrue(1 <= retry_val <= 60)


if __name__ == "__main__":
    unittest.main()
