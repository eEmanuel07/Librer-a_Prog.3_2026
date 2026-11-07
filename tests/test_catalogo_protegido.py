"""Tests de protección RBAC y paginación en editoriales, géneros y autores (issue #51, [R7])."""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import app.modules.clientes.models  # noqa: F401
import app.modules.ventas.models  # noqa: F401
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.paginacion import PaginaInexistente
from app.core.security import crear_access_token
from app.modules.autores.models import Autor
from app.modules.autores.router import router as autores_router
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.router import router as editoriales_router
from app.modules.generos.models import Genero
from app.modules.generos.router import router as generos_router
from app.modules.libros.models import Libro, LibroAutor
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


class TestCatalogoProtegidoYPaginado(unittest.IsolatedAsyncioTestCase):
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

        self.app.include_router(editoriales_router)
        self.app.include_router(generos_router)
        self.app.include_router(autores_router)

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
                nombre="Admin",
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
            ed = Editorial(id=1, nombre="Sudamericana", pais="Argentina")
            gen = Genero(id=1, nombre="Novela")
            aut = Autor(id=1, nombre="Julio Cortázar", nacionalidad="Argentina")
            s.add_all([ed, gen, aut])
            s.commit()

            libro_vigente = Libro(
                id=1,
                isbn="978-1",
                titulo="Rayuela",
                precio=Decimal("25000.00"),
                stock=10,
                editorial_id=1,
                genero_id=1,
                borrado_en=None,
            )
            libro_baja = Libro(
                id=2,
                isbn="978-2",
                titulo="Libro Dado de Baja",
                precio=Decimal("15000.00"),
                stock=0,
                editorial_id=1,
                genero_id=1,
                borrado_en=datetime.now(timezone.utc),
            )
            s.add_all([libro_vigente, libro_baja])
            s.commit()
            s.add_all(
                [
                    LibroAutor(libro_id=1, autor_id=1, rol="autor", orden=1),
                    LibroAutor(libro_id=2, autor_id=1, rol="autor", orden=1),
                ]
            )
            s.commit()

        self.token_admin = crear_access_token(1, ["ADMIN"], settings=self.settings)
        self.token_vendedor = crear_access_token(2, ["VENDEDOR"], settings=self.settings)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_c06_escrituras_sin_sesion_dan_401_y_vendedor_da_403(self):
        rutas_post = [
            ("/editoriales/", {"nombre": "Emecé", "pais": "Argentina"}),
            ("/generos/", {"nombre": "Cuento"}),
            ("/autores/", {"nombre": "Jorge Luis Borges", "nacionalidad": "Argentina"}),
        ]
        for url, payload in rutas_post:
            with self.subTest(url=url):
                r_401 = self.client.post(url, json=payload)
                self.assertEqual(r_401.status_code, 401)
                r_403 = self.client.post(
                    url, json=payload, cookies={"access_token": self.token_vendedor}
                )
                self.assertEqual(r_403.status_code, 403)

        rutas_patch = [
            ("/editoriales/1", {"pais": "Uruguay"}),
            ("/autores/1", {"nacionalidad": "Bélgica"}),
        ]
        for url, payload in rutas_patch:
            with self.subTest(url=url):
                r_401 = self.client.patch(url, json=payload)
                self.assertEqual(r_401.status_code, 401)
                r_403 = self.client.patch(
                    url, json=payload, cookies={"access_token": self.token_vendedor}
                )
                self.assertEqual(r_403.status_code, 403)

    async def test_02_admin_crea_actualiza_y_unicidad_da_409(self):
        # Crear editorial con ADMIN -> 201
        r_ed = self.client.post(
            "/editoriales/",
            json={"nombre": "Emecé", "pais": "Argentina"},
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(r_ed.status_code, 201)

        # Nombre duplicado -> 409
        r_ed_dup = self.client.post(
            "/editoriales/",
            json={"nombre": "Emecé", "pais": "Chile"},
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(r_ed_dup.status_code, 409)

        # PATCH parcial (exclude_unset) -> 200
        r_patch = self.client.patch(
            "/editoriales/1",
            json={"pais": "España"},
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(r_patch.status_code, 200)
        self.assertEqual(r_patch.json()["nombre"], "Sudamericana")
        self.assertEqual(r_patch.json()["pais"], "España")

        # Crear género duplicado -> 409
        r_gen_dup = self.client.post(
            "/generos/",
            json={"nombre": "Novela"},
            cookies={"access_token": self.token_admin},
        )
        self.assertEqual(r_gen_dup.status_code, 409)

    async def test_03_get_publicos_con_envoltorio_y_filtran_borrado_logico(self):
        # GET /editoriales/ sin sesión -> 200 con envoltorio Pagina
        r_eds = self.client.get("/editoriales/?page=1&size=10")
        self.assertEqual(r_eds.status_code, 200)
        body_eds = r_eds.json()
        self.assertEqual(body_eds["total"], 1)
        self.assertEqual(body_eds["page"], 1)
        self.assertEqual(body_eds["pages"], 1)
        self.assertEqual(len(body_eds["items"]), 1)

        # GET /generos/ sin sesión -> 200 con envoltorio Pagina
        r_gens = self.client.get("/generos/?page=1&size=10")
        self.assertEqual(r_gens.status_code, 200)
        self.assertEqual(r_gens.json()["total"], 1)

        # GET /{id}/libros en editoriales, géneros y autores excluye el libro dado de baja
        for url in ("/editoriales/1/libros", "/generos/1/libros", "/autores/1/libros"):
            with self.subTest(url=url):
                r_libros = self.client.get(url)
                self.assertEqual(r_libros.status_code, 200)
                pagina = r_libros.json()
                self.assertEqual(pagina["total"], 1)
                self.assertEqual(len(pagina["items"]), 1)
                self.assertEqual(pagina["items"][0]["titulo"], "Rayuela")

        # Página inexistente -> 422
        r_422 = self.client.get("/editoriales/?page=5&size=10")
        self.assertEqual(r_422.status_code, 422)


if __name__ == "__main__":
    unittest.main()
