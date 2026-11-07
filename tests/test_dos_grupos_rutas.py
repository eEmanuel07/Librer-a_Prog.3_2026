"""Tests de los dos grupos de rutas en main.py y cambio obligatorio de contraseña (issue #47, [R3])."""

import unittest

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import crear_access_token, hashear_password
from app.main import app
from app.modules.editoriales.models import Editorial
from app.modules.usuarios.models import AsignacionRol, Usuario


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


class TestDosGruposRutasYCambioObligatorio(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _make_settings()

        async def override_get_session():
            with Session(self.engine, expire_on_commit=False) as s:
                yield _AsyncSessionAdapter(s)

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[get_settings] = lambda: self.settings

        self.client = TestClient(app)

        hash_provisorio = await hashear_password("Provisoria123!", settings=self.settings)
        with Session(self.engine) as s:
            s.add(Editorial(id=1, nombre="Sudamericana", pais="Argentina"))
            nuevo = Usuario(
                id=1,
                email="nuevo@example.com",
                nombre="Nuevo Vendedor",
                password_hash=hash_provisorio,
                activo=True,
                debe_cambiar_password=True,
            )
            admin_pendiente = Usuario(
                id=2,
                email="admin_nuevo@example.com",
                nombre="Admin Con Cambio Pendiente",
                password_hash=hash_provisorio,
                activo=True,
                debe_cambiar_password=True,
            )
            s.add_all([nuevo, admin_pendiente])
            s.commit()
            s.add_all(
                [
                    AsignacionRol(usuario_id=1, rol="VENDEDOR"),
                    AsignacionRol(usuario_id=2, rol="ADMIN"),
                ]
            )
            s.commit()

        self.token_nuevo = crear_access_token(1, ["VENDEDOR"], settings=self.settings)
        self.token_admin_pendiente = crear_access_token(2, ["ADMIN"], settings=self.settings)

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    async def test_01_c09_bloqueado_en_grupo_protegido_salvo_auth_y_abiertas_y_200_tras_cambio(self):
        # 1. Con debe_cambiar_password=True puede usar /auth/yo y rutas abiertas (GET /editoriales/)
        r_yo = self.client.get("/auth/yo", cookies={"access_token": self.token_nuevo})
        self.assertEqual(r_yo.status_code, 200)
        self.assertTrue(r_yo.json()["debe_cambiar_password"])

        r_abierta = self.client.get("/editoriales/", cookies={"access_token": self.token_nuevo})
        self.assertEqual(r_abierta.status_code, 200)

        # 2. En el grupo protegido recibe 403 (incluso en /mis-ventas, /ventas/ o /eventos)
        for ruta in ("/mis-ventas", "/ventas/"):
            with self.subTest(ruta=ruta):
                r_bloqueado = self.client.get(ruta, cookies={"access_token": self.token_nuevo})
                self.assertEqual(r_bloqueado.status_code, 403)

        r_admin_bloqueado = self.client.get(
            "/eventos", cookies={"access_token": self.token_admin_pendiente}
        )
        self.assertEqual(r_admin_bloqueado.status_code, 403)

        # 3. Cambia su contraseña en /auth/cambiar-password (grupo abierto)
        r_cambio = self.client.post(
            "/auth/cambiar-password",
            json={
                "password_actual": "Provisoria123!",
                "password_nueva": "Definitiva456!",
            },
            cookies={"access_token": self.token_nuevo},
        )
        self.assertEqual(r_cambio.status_code, 200)

        # 4. Después del cambio, con la misma sesión responde 200 en el grupo protegido
        r_desbloqueado_mis_ventas = self.client.get(
            "/mis-ventas", cookies={"access_token": self.token_nuevo}
        )
        self.assertEqual(r_desbloqueado_mis_ventas.status_code, 200)

        r_desbloqueado_ventas = self.client.get(
            "/ventas/", cookies={"access_token": self.token_nuevo}
        )
        self.assertEqual(r_desbloqueado_ventas.status_code, 200)


if __name__ == "__main__":
    unittest.main()
