import unittest
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
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
from app.core.security import crear_access_token
from app.modules.usuarios.models import Usuario


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


class TestAuthDependencies(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _make_settings()

        self.app = FastAPI()

        @self.app.get("/ruta-protegida")
        async def ruta_protegida(usuario: Usuario = Depends(get_usuario_actual)):
            return {"id": usuario.id, "email": usuario.email}

        async def override_get_session():
            with Session(self.engine, expire_on_commit=False) as s:
                yield _AsyncSessionAdapter(s)

        self.app.dependency_overrides[get_session] = override_get_session
        self.app.dependency_overrides[get_settings] = lambda: self.settings

        self.client = TestClient(self.app)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_sin_cookie_retorna_401(self):
        resp = self.client.get("/ruta-protegida")
        self.assertEqual(resp.status_code, 401)

    async def test_02_token_invalido_retorna_401(self):
        resp = self.client.get("/ruta-protegida", cookies={"access_token": "token-basura"})
        self.assertEqual(resp.status_code, 401)

    async def test_03_token_vencido_retorna_401(self):
        hace_una_hora = datetime.now(timezone.utc) - timedelta(hours=1)
        token_vencido = crear_access_token(1, ["CLIENTE"], settings=self.settings, ahora=hace_una_hora)
        resp = self.client.get("/ruta-protegida", cookies={"access_token": token_vencido})
        self.assertEqual(resp.status_code, 401)

    async def test_04_usuario_inexistente_en_base_retorna_401(self):
        token = crear_access_token(999, ["CLIENTE"], settings=self.settings)
        resp = self.client.get("/ruta-protegida", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 401)

    async def test_05_usuario_inactivo_retorna_401(self):
        with Session(self.engine) as s:
            u = Usuario(
                id=2,
                nombre="Inactivo",
                email="inactivo@example.com",
                password_hash="fakehash",
                activo=False,
            )
            s.add(u)
            s.commit()

        token = crear_access_token(2, ["CLIENTE"], settings=self.settings)
        resp = self.client.get("/ruta-protegida", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 401)

    async def test_06_usuario_activo_autentica_exitosamente(self):
        with Session(self.engine) as s:
            u = Usuario(
                id=1,
                nombre="Usuario Valido",
                email="valido@example.com",
                password_hash="fakehash",
                activo=True,
            )
            s.add(u)
            s.commit()

        token = crear_access_token(1, ["CLIENTE"], settings=self.settings)
        resp = self.client.get("/ruta-protegida", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"id": 1, "email": "valido@example.com"})


if __name__ == "__main__":
    unittest.main()
