"""Tests de roles con vigencia: asignar, listar y revocar (issue #49, [R5])."""

import unittest
from datetime import datetime, timedelta, timezone

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
from app.core.security import crear_access_token
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from app.modules.usuarios.router import router as auth_router
from app.modules.usuarios.router import router_usuarios
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


class TestRolesVigencia(unittest.IsolatedAsyncioTestCase):
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

        # Crear admin1 (id=1), admin2 (id=2) y vendedor (id=3)
        with Session(self.engine) as s:
            u1 = Usuario(
                id=1,
                email="admin@example.com",
                nombre="Admin Uno",
                password_hash="hash",
                activo=True,
            )
            u2 = Usuario(
                id=2,
                email="admin2@example.com",
                nombre="Admin Dos",
                password_hash="hash",
                activo=True,
            )
            u3 = Usuario(
                id=3,
                email="vendedor@example.com",
                nombre="Vendedor",
                password_hash="hash",
                activo=True,
            )
            s.add_all([u1, u2, u3])
            s.commit()
            s.add_all(
                [
                    AsignacionRol(usuario_id=1, rol="ADMIN"),
                    AsignacionRol(usuario_id=2, rol="ADMIN"),
                    AsignacionRol(usuario_id=3, rol="VENDEDOR"),
                ]
            )
            s.commit()

        self.token_admin1 = crear_access_token(1, ["ADMIN"], settings=self.settings)
        self.token_admin2 = crear_access_token(2, ["ADMIN"], settings=self.settings)
        self.token_vendedor = crear_access_token(3, ["VENDEDOR"], settings=self.settings)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_asignar_rol_con_vencimiento_futuro_crea_asignacion_y_evento(self):
        manana = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        resp = self.client.post(
            "/usuarios/3/roles",
            json={"rol": "ADMIN", "vence_en": manana},
            cookies={"access_token": self.token_admin1},
        )
        self.assertEqual(resp.status_code, 201)
        datos = resp.json()
        self.assertEqual(datos["usuario_id"], 3)
        self.assertEqual(datos["rol"], "ADMIN")
        self.assertEqual(datos["otorgada_por"], 1)
        self.assertIsNotNone(datos["vence_en"])
        self.assertIsNone(datos["revocada_en"])
        self.assertTrue(datos["vigente"])

        with Session(self.engine) as s:
            eventos = s.exec(select(EventoSeguridad)).all()
            self.assertEqual(len(eventos), 1)
            self.assertEqual(eventos[0].actor, "admin@example.com")
            self.assertIn("ADMIN", eventos[0].accion)

    async def test_02_c07_c08_vencimiento_en_el_pasado_o_sin_zona_horaria_da_422(self):
        ayer = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        resp_pasado = self.client.post(
            "/usuarios/3/roles",
            json={"rol": "ADMIN", "vence_en": ayer},
            cookies={"access_token": self.token_admin1},
        )
        self.assertEqual(resp_pasado.status_code, 422)

        sin_zona = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
        resp_sin_zona = self.client.post(
            "/usuarios/3/roles",
            json={"rol": "ADMIN", "vence_en": sin_zona},
            cookies={"access_token": self.token_admin1},
        )
        self.assertEqual(resp_sin_zona.status_code, 422)

    async def test_03_asignar_rol_ya_vigente_da_409_rn03(self):
        resp = self.client.post(
            "/usuarios/3/roles",
            json={"rol": "VENDEDOR"},
            cookies={"access_token": self.token_admin1},
        )
        self.assertEqual(resp.status_code, 409)

    async def test_04_reasignar_rol_vencido_cierra_fila_anterior_y_abre_nueva(self):
        hace_una_hora = datetime.now(timezone.utc) - timedelta(hours=1)
        with Session(self.engine) as s:
            s.add(
                AsignacionRol(
                    usuario_id=3,
                    rol="CLIENTE",
                    desde=hace_una_hora - timedelta(hours=2),
                    vence_en=hace_una_hora,
                    revocada_en=None,
                )
            )
            s.commit()

        manana = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        resp = self.client.post(
            "/usuarios/3/roles",
            json={"rol": "CLIENTE", "vence_en": manana},
            cookies={"access_token": self.token_admin1},
        )
        self.assertEqual(resp.status_code, 201)

        with Session(self.engine) as s:
            filas = s.exec(
                select(AsignacionRol)
                .where(AsignacionRol.usuario_id == 3, AsignacionRol.rol == "CLIENTE")
                .order_by(AsignacionRol.id)
            ).all()
            self.assertEqual(len(filas), 2)
            self.assertIsNotNone(filas[0].revocada_en)
            self.assertIsNone(filas[1].revocada_en)

    async def test_05_c07_revocar_rol_escribe_revocada_en_conserva_fila_y_corta_sesion_abierta(self):
        # admin1 revoca ADMIN de admin2 mientras admin2 tiene sesión abierta
        resp = self.client.delete(
            "/usuarios/2/roles/ADMIN",
            cookies={"access_token": self.token_admin1},
        )
        self.assertEqual(resp.status_code, 200)
        datos = resp.json()
        self.assertIsNotNone(datos["revocada_en"])
        self.assertFalse(datos["vigente"])

        # La fila no se borró
        with Session(self.engine) as s:
            filas = s.exec(
                select(AsignacionRol).where(
                    AsignacionRol.usuario_id == 2, AsignacionRol.rol == "ADMIN"
                )
            ).all()
            self.assertEqual(len(filas), 1)
            self.assertIsNotNone(filas[0].revocada_en)
            eventos = s.exec(select(EventoSeguridad)).all()
            self.assertEqual(len(eventos), 1)

        # Petición siguiente de admin2 con su token abierto -> 403 (C-07)
        resp_admin2 = self.client.get(
            "/usuarios/3/roles",
            cookies={"access_token": self.token_admin2},
        )
        self.assertEqual(resp_admin2.status_code, 403)

    async def test_06_c08_rn05_autoproteccion_admin_no_se_revoca_su_propio_admin_409(self):
        resp = self.client.delete(
            "/usuarios/1/roles/ADMIN",
            cookies={"access_token": self.token_admin1},
        )
        self.assertEqual(resp.status_code, 409)

    async def test_07_listar_roles_de_usuario_devuelve_historial_completo(self):
        self.client.delete(
            "/usuarios/2/roles/ADMIN",
            cookies={"access_token": self.token_admin1},
        )
        resp = self.client.get(
            "/usuarios/2/roles",
            cookies={"access_token": self.token_admin1},
        )
        self.assertEqual(resp.status_code, 200)
        lista = resp.json()
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]["rol"], "ADMIN")
        self.assertIsNotNone(lista[0]["revocada_en"])
        self.assertFalse(lista[0]["vigente"])

    async def test_08_usuario_inexistente_da_404_y_vendedor_da_403(self):
        resp_404 = self.client.get(
            "/usuarios/999/roles",
            cookies={"access_token": self.token_admin1},
        )
        self.assertEqual(resp_404.status_code, 404)

        resp_403 = self.client.post(
            "/usuarios/3/roles",
            json={"rol": "ADMIN"},
            cookies={"access_token": self.token_vendedor},
        )
        self.assertEqual(resp_403.status_code, 403)


if __name__ == "__main__":
    unittest.main()
