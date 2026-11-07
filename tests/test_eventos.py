"""Tests de GET /eventos paginado (issue #50, [R6])."""

import unittest

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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
from app.core.paginacion import PaginaInexistente
from app.core.security import crear_access_token
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from app.modules.usuarios.router import router as auth_router
from app.modules.usuarios.router import router_eventos, router_usuarios


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


class TestEventosPaginado(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _make_settings()

        self.app = FastAPI()

        @self.app.exception_handler(PaginaInexistente)
        async def pagina_inexistente(_request: Request, error: PaginaInexistente) -> JSONResponse:
            return JSONResponse(status_code=422, content={"detail": error.mensaje})

        self.app.include_router(auth_router)
        self.app.include_router(router_usuarios)
        self.app.include_router(router_eventos)

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
            s.add(
                EventoSeguridad(
                    actor="SISTEMA",
                    accion="Carga de los datos iniciales",
                )
            )
            s.commit()

        self.token_admin = crear_access_token(1, ["ADMIN"], settings=self.settings)
        self.token_vendedor = crear_access_token(2, ["VENDEDOR"], settings=self.settings)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_lista_altas_cambios_de_rol_y_evento_sistema_con_envoltorio(self):
        # Alta de personal -> deja evento 2
        resp_alta = self.client.post(
            "/usuarios",
            json={
                "nombre": "Nuevo",
                "email": "nuevo@example.com",
                "password": "Provisoria123!",
            },
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(resp_alta.status_code, 201)
        nuevo_id = resp_alta.json()["id"]

        # Asignar rol -> deja evento 3
        resp_rol = self.client.post(
            f"/usuarios/{nuevo_id}/roles",
            json={"rol": "VENDEDOR"},
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(resp_rol.status_code, 201)

        # Consultar primera página con size=2
        resp = self.client.get(
            "/eventos?page=1&size=2",
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(resp.status_code, 200)
        pagina = resp.json()
        self.assertEqual(pagina["total"], 3)
        self.assertEqual(pagina["page"], 1)
        self.assertEqual(pagina["size"], 2)
        self.assertEqual(pagina["pages"], 2)
        self.assertEqual(len(pagina["items"]), 2)
        self.assertEqual(pagina["items"][0]["actor"], "SISTEMA")

        # Consultar segunda página
        resp2 = self.client.get(
            "/eventos?page=2&size=2",
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(resp2.status_code, 200)
        pagina2 = resp2.json()
        self.assertEqual(len(pagina2["items"]), 1)
        self.assertIn("VENDEDOR", pagina2["items"][0]["accion"])

    async def test_02_pagina_mas_alla_de_la_ultima_da_422(self):
        resp = self.client.get(
            "/eventos?page=99&size=20",
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(resp.status_code, 422)

    async def test_03_vendedor_recibe_403_y_sin_sesion_401(self):
        resp_403 = self.client.get(
            "/eventos",
            cookies={"access_token": self.token_vendedor},
        )
        self.assertEqual(resp_403.status_code, 403)

        resp_401 = self.client.get("/eventos")
        self.assertEqual(resp_401.status_code, 401)


if __name__ == "__main__":
    unittest.main()
