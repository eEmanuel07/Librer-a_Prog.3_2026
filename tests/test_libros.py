"""Tests del catálogo de libros (E4, issue #23): alta con stock inicial, PATCH,
baja lógica, reutilización del ISBN y listado con envoltorio.

Corren contra SQLite en memoria, sin PostgreSQL, igual que los de autenticación.
Las claves foráneas se activan con PRAGMA porque SQLite no las controla por
defecto. El disparador de sólo agregado y los códigos de error de PostgreSQL no
se ven acá: se prueban contra PostgreSQL (caso C-14 y los .http de E7).
"""

import asyncio
import unittest
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.dependencies import get_usuario_actual
from app.main import app
from app.modules.autores.models import Autor
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, MovimientoStock
from app.modules.libros.repository import LibroRepository
from app.modules.usuarios.models import AsignacionRol, Usuario


def _settings() -> Settings:
    return Settings(
        postgres_password="secret-db-password",
        jwt_secret="a" * 32,
        bcrypt_costo=4,
    )


class _SesionAsync:
    """Envuelve una sesión sincrónica de SQLite con la interfaz async que usa la app."""

    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def add(self, obj) -> None:
        self._s.add(obj)

    async def flush(self) -> None:
        self._s.flush()

    async def commit(self) -> None:
        self._s.commit()

    async def rollback(self) -> None:
        self._s.rollback()

    async def exec(self, statement):
        return self._s.exec(statement)

    async def get(self, modelo, ident):
        return self._s.get(modelo, ident)


def _alta(**cambios) -> dict:
    cuerpo = {
        "isbn": "978-950-00-0006-6",
        "titulo": "Los que aman, odian",
        "precio": "21000.00",
        "stock_inicial": 4,
        "editorial_id": 1,
        "genero_id": 1,
        "autores": [
            {"autor_id": 2, "rol": "coautor", "orden": 2},
            {"autor_id": 1, "rol": "coautor", "orden": 1},
        ],
    }
    cuerpo.update(cambios)
    return cuerpo


class _BaseLibros(unittest.TestCase):
    def setUp(self) -> None:
        self.motor = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )

        @event.listens_for(self.motor, "connect")
        def _claves_foraneas(conexion, _registro) -> None:
            conexion.execute("PRAGMA foreign_keys=ON")

        SQLModel.metadata.create_all(self.motor)
        with Session(self.motor) as s:
            s.add(Editorial(nombre="Sudamericana", pais="AR"))
            s.add(Genero(nombre="Novela"))
            s.add(Autor(nombre="Silvina Ocampo", nacionalidad="AR"))
            s.add(Autor(nombre="Adolfo Bioy Casares", nacionalidad="AR"))
            admin = Usuario(
                email="admin@libreria.local",
                nombre="Admin",
                password_hash="no-es-un-hash",
                activo=True,
                debe_cambiar_password=False,
            )
            vendedor = Usuario(
                email="vendedor@libreria.local",
                nombre="Vendedor",
                password_hash="no-es-un-hash",
                activo=True,
                debe_cambiar_password=False,
            )
            s.add_all([admin, vendedor])
            s.flush()
            # requiere_rol consulta los roles vigentes en la base (RN-04), no en el token.
            s.add_all([
                AsignacionRol(usuario_id=admin.id, rol="ADMIN"),
                AsignacionRol(usuario_id=vendedor.id, rol="VENDEDOR"),
            ])
            s.commit()
            self.usuario = s.exec(select(Usuario).where(Usuario.email == admin.email)).one()
            self.vendedor = s.exec(select(Usuario).where(Usuario.email == vendedor.email)).one()

        async def sesion_de_prueba():
            with Session(self.motor, expire_on_commit=False) as s:
                yield _SesionAsync(s)

        app.dependency_overrides[get_session] = sesion_de_prueba
        app.dependency_overrides[get_settings] = _settings
        app.dependency_overrides[get_usuario_actual] = lambda: self.usuario
        self.cliente = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.motor.dispose()

    # ---------- ayudas ----------

    def _movimientos(self, libro_id: int) -> list[MovimientoStock]:
        with Session(self.motor) as s:
            return list(s.exec(select(MovimientoStock).where(MovimientoStock.libro_id == libro_id)))

    def _libros_en_tabla(self) -> list[Libro]:
        with Session(self.motor) as s:
            return list(s.exec(select(Libro)))

    def _crear(self, **cambios) -> dict:
        r = self.cliente.post("/libros/", json=_alta(**cambios))
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()


class TestAltaDeLibro(_BaseLibros):
    def test_alta_con_stock_inicial_deja_un_movimiento_stock_inicial(self) -> None:
        r = self.cliente.post("/libros/", json=_alta())

        self.assertEqual(r.status_code, 201, r.text)
        libro = r.json()
        self.assertEqual(libro["stock"], 4)
        self.assertEqual([a["autor"]["nombre"] for a in libro["autores"]],
                         ["Silvina Ocampo", "Adolfo Bioy Casares"])
        movimientos = self._movimientos(libro["id"])
        self.assertEqual(len(movimientos), 1)
        self.assertEqual(movimientos[0].cantidad, 4)
        self.assertEqual(movimientos[0].motivo, "Stock inicial")
        self.assertEqual(movimientos[0].usuario_id, self.usuario.id)
        self.assertIsNone(movimientos[0].venta_id)

    def test_alta_con_stock_inicial_cero_no_deja_movimiento(self) -> None:
        libro = self._crear(stock_inicial=0)

        self.assertEqual(libro["stock"], 0)
        self.assertEqual(self._movimientos(libro["id"]), [])

    def test_el_stock_queda_igual_a_la_suma_de_movimientos(self) -> None:
        self._crear()
        self._crear(isbn="978-950-00-0007-3", stock_inicial=0)

        # RN-11: la misma comprobación que usa el caso C-11.
        async def _inconsistentes():
            with Session(self.motor) as s:
                return await LibroRepository(_SesionAsync(s)).ids_con_stock_inconsistente()

        self.assertEqual(asyncio.run(_inconsistentes()), [])

    def test_el_alta_rechaza_stock_y_stock_inicial_negativo(self) -> None:
        cuerpo_con_stock = _alta()
        del cuerpo_con_stock["stock_inicial"]
        cuerpo_con_stock["stock"] = 4

        for cuerpo in (cuerpo_con_stock, _alta(stock_inicial=-1)):
            with self.subTest(cuerpo=cuerpo):
                r = self.cliente.post("/libros/", json=cuerpo)
                self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(self._libros_en_tabla(), [])

    def test_isbn_de_un_vigente_da_409_sin_escribir_nada(self) -> None:
        primero = self._crear()

        r = self.cliente.post("/libros/", json=_alta(titulo="Otro título"))

        self.assertEqual(r.status_code, 409, r.text)
        self.assertEqual(len(self._libros_en_tabla()), 1)
        self.assertEqual(len(self._movimientos(primero["id"])), 1)

    def test_editorial_inexistente_da_409_sin_libro_ni_movimiento(self) -> None:
        r = self.cliente.post("/libros/", json=_alta(editorial_id=999))

        self.assertEqual(r.status_code, 409, r.text)
        self.assertNotIn("FOREIGN KEY", r.text)
        self.assertEqual(self._libros_en_tabla(), [])
        with Session(self.motor) as s:
            self.assertEqual(list(s.exec(select(MovimientoStock))), [])


class TestPatchDeLibro(_BaseLibros):
    def test_patch_parcial_cambia_solo_lo_enviado(self) -> None:
        libro = self._crear()

        r = self.cliente.patch(f"/libros/{libro['id']}", json={"precio": "25000.00"})

        self.assertEqual(r.status_code, 200, r.text)
        cambiado = r.json()
        self.assertEqual(Decimal(cambiado["precio"]), Decimal("25000.00"))
        self.assertEqual(cambiado["titulo"], libro["titulo"])
        self.assertEqual(cambiado["stock"], 4)
        self.assertEqual(len(cambiado["autores"]), 2)

    def test_patch_del_stock_u_otro_campo_da_422(self) -> None:
        libro = self._crear()

        for cuerpo in ({"stock": 100}, {"isbn": "111"}, {"editorial_id": 1}, {"titulo": None}):
            with self.subTest(cuerpo=cuerpo):
                r = self.cliente.patch(f"/libros/{libro['id']}", json=cuerpo)
                self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(self._libros_en_tabla()[0].stock, 4)

    def test_patch_de_un_libro_inexistente_o_dado_de_baja_da_404(self) -> None:
        libro = self._crear()
        self.cliente.delete(f"/libros/{libro['id']}")

        for libro_id in (999, libro["id"]):
            with self.subTest(libro_id=libro_id):
                r = self.cliente.patch(f"/libros/{libro_id}", json={"titulo": "Nuevo"})
                self.assertEqual(r.status_code, 404, r.text)


class TestBajaDeLibro(_BaseLibros):
    def test_baja_responde_204_y_el_libro_sale_del_catalogo(self) -> None:
        libro = self._crear()

        r = self.cliente.delete(f"/libros/{libro['id']}")

        self.assertEqual(r.status_code, 204, r.text)
        self.assertEqual(r.content, b"")
        fila = self._libros_en_tabla()[0]
        self.assertIsNotNone(fila.borrado_en)  # la fila sigue en la tabla
        self.assertEqual(self.cliente.get(f"/libros/{libro['id']}").status_code, 404)
        self.assertEqual(self.cliente.get("/libros/").json()["total"], 0)

    def test_baja_repetida_o_de_un_inexistente_da_404(self) -> None:
        libro = self._crear()
        self.cliente.delete(f"/libros/{libro['id']}")

        for libro_id in (libro["id"], 999):
            with self.subTest(libro_id=libro_id):
                self.assertEqual(self.cliente.delete(f"/libros/{libro_id}").status_code, 404)

    def test_el_isbn_de_un_libro_dado_de_baja_se_puede_volver_a_cargar(self) -> None:
        viejo = self._crear()
        self.cliente.delete(f"/libros/{viejo['id']}")

        nuevo = self.cliente.post("/libros/", json=_alta())
        repetido = self.cliente.post("/libros/", json=_alta())

        self.assertEqual(nuevo.status_code, 201, nuevo.text)
        self.assertNotEqual(nuevo.json()["id"], viejo["id"])
        self.assertEqual(repetido.status_code, 409, repetido.text)


class TestSesionEnEscrituras(_BaseLibros):
    def test_sin_sesion_alta_patch_y_baja_dan_401_sin_escribir(self) -> None:
        libro = self._crear()
        del app.dependency_overrides[get_usuario_actual]  # sin cookie

        respuestas = [
            self.cliente.post("/libros/", json=_alta(isbn="978-950-00-0099-9")),
            self.cliente.patch(f"/libros/{libro['id']}", json={"titulo": "Nuevo"}),
            self.cliente.delete(f"/libros/{libro['id']}"),
        ]

        self.assertEqual([r.status_code for r in respuestas], [401, 401, 401])
        filas = self._libros_en_tabla()
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0].titulo, libro["titulo"])
        self.assertIsNone(filas[0].borrado_en)


class TestListadoDeLibros(_BaseLibros):
    def setUp(self) -> None:
        super().setUp()
        self._crear(isbn="1", titulo="Ficciones", autores=[])
        self._crear(isbn="2", titulo="Rayuela", genero_id=None, autores=[])
        self._crear(isbn="3", titulo="El Aleph", autores=[])

    def test_listado_con_envoltorio(self) -> None:
        r = self.cliente.get("/libros/", params={"size": 2})

        self.assertEqual(r.status_code, 200, r.text)
        cuerpo = r.json()
        self.assertEqual({k: cuerpo[k] for k in ("total", "page", "size", "pages")},
                         {"total": 3, "page": 1, "size": 2, "pages": 2})
        self.assertEqual([l["titulo"] for l in cuerpo["items"]], ["Ficciones", "Rayuela"])

    def test_busqueda_con_inyeccion_devuelve_lista_vacia(self) -> None:
        r = self.cliente.get("/libros/", params={"titulo": "' OR '1'='1"})

        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual((r.json()["items"], r.json()["total"]), ([], 0))

    def test_paginacion_con_filtro_y_pagina_inexistente(self) -> None:
        r = self.cliente.get("/libros/", params={"titulo": "FICC", "size": 1})
        fuera = self.cliente.get("/libros/", params={"titulo": "ficc", "size": 1, "page": 2})
        grande = self.cliente.get("/libros/", params={"size": 500})

        self.assertEqual((r.json()["total"], r.json()["pages"]), (1, 1))
        self.assertEqual(fuera.status_code, 422, fuera.text)
        self.assertEqual(fuera.json()["detail"], "La página 2 no existe: hay 1")
        self.assertEqual(grande.status_code, 422)

    def test_filtro_por_genero_cuenta_con_el_mismo_filtro(self) -> None:
        r = self.cliente.get("/libros/", params={"genero_id": 1})

        self.assertEqual(r.json()["total"], 2)
        self.assertEqual({l["titulo"] for l in r.json()["items"]}, {"Ficciones", "El Aleph"})


class TestReposicion(_BaseLibros):
    """E5 (#24): POST /libros/{id}/reponer."""

    def test_reponer_suma_el_stock_y_deja_el_movimiento(self) -> None:
        libro = self._crear()  # stock_inicial 4

        r = self.cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 3})

        self.assertEqual(r.status_code, 200, r.text)
        cuerpo = r.json()
        self.assertEqual(cuerpo["libro"]["stock"], 7)
        self.assertEqual(cuerpo["libro"]["id"], libro["id"])
        self.assertEqual((cuerpo["movimiento"]["cantidad"], cuerpo["movimiento"]["motivo"]), (3, "Reposición"))
        self.assertEqual(cuerpo["movimiento"]["usuario_id"], self.usuario.id)
        movimientos = self._movimientos(libro["id"])
        self.assertEqual(sorted(m.cantidad for m in movimientos), [3, 4])
        self.assertEqual(self._libros_en_tabla()[0].stock, sum(m.cantidad for m in movimientos))

    def test_cantidad_invalida_da_422_sin_tocar_el_stock(self) -> None:
        libro = self._crear()

        for cuerpo in ({"cantidad": 0}, {"cantidad": -2}, {"cantidad": 1, "motivo": "venta"}, {}):
            with self.subTest(cuerpo=cuerpo):
                r = self.cliente.post(f"/libros/{libro['id']}/reponer", json=cuerpo)
                self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(self._libros_en_tabla()[0].stock, 4)
        self.assertEqual(len(self._movimientos(libro["id"])), 1)

    def test_reponer_un_libro_dado_de_baja_da_409_sin_movimiento(self) -> None:
        libro = self._crear()
        self.cliente.delete(f"/libros/{libro['id']}")

        r = self.cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 3})

        self.assertEqual(r.status_code, 409, r.text)
        self.assertEqual(r.json()["detail"], "El libro está dado de baja")
        self.assertEqual(len(self._movimientos(libro["id"])), 1)
        self.assertEqual(self._libros_en_tabla()[0].stock, 4)

    def test_reponer_un_libro_inexistente_da_404(self) -> None:
        r = self.cliente.post("/libros/999/reponer", json={"cantidad": 3})

        self.assertEqual(r.status_code, 404, r.text)
        self.assertEqual(r.json()["detail"], "El libro no existe")  # no el 404 de ruta inexistente


class TestMovimientos(_BaseLibros):
    """E5 (#24): GET /libros/{id}/movimientos."""

    def test_movimientos_en_orden_con_envoltorio(self) -> None:
        libro = self._crear()
        self.cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 2})
        self.cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 5})

        r = self.cliente.get(f"/libros/{libro['id']}/movimientos")

        self.assertEqual(r.status_code, 200, r.text)
        cuerpo = r.json()
        self.assertEqual((cuerpo["total"], cuerpo["page"], cuerpo["pages"]), (3, 1, 1))
        self.assertEqual([(m["motivo"], m["cantidad"]) for m in cuerpo["items"]],
                         [("Stock inicial", 4), ("Reposición", 2), ("Reposición", 5)])

    def test_paginacion_de_movimientos(self) -> None:
        libro = self._crear()
        self.cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 2})

        segunda = self.cliente.get(f"/libros/{libro['id']}/movimientos", params={"size": 1, "page": 2})
        fuera = self.cliente.get(f"/libros/{libro['id']}/movimientos", params={"size": 1, "page": 3})

        self.assertEqual(segunda.status_code, 200, segunda.text)
        self.assertEqual([m["cantidad"] for m in segunda.json()["items"]], [2])
        self.assertEqual(fuera.status_code, 422, fuera.text)

    def test_un_libro_dado_de_baja_sigue_mostrando_sus_movimientos(self) -> None:
        libro = self._crear()
        self.cliente.delete(f"/libros/{libro['id']}")

        r = self.cliente.get(f"/libros/{libro['id']}/movimientos")

        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["total"], 1)

    def test_movimientos_de_un_libro_inexistente_da_404(self) -> None:
        r = self.cliente.get("/libros/999/movimientos")

        self.assertEqual(r.status_code, 404, r.text)
        self.assertEqual(r.json()["detail"], "El libro no existe")

    def test_sin_sesion_reponer_y_movimientos_dan_401(self) -> None:
        libro = self._crear()
        del app.dependency_overrides[get_usuario_actual]

        reponer = self.cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 3})
        movimientos = self.cliente.get(f"/libros/{libro['id']}/movimientos")

        self.assertEqual((reponer.status_code, movimientos.status_code), (401, 401))
        self.assertEqual(self._libros_en_tabla()[0].stock, 4)


class TestRolAdmin(_BaseLibros):
    """Las escrituras de libros, la reposición y los movimientos son de ADMIN (RN-04)."""

    def _como_vendedor(self) -> None:
        app.dependency_overrides[get_usuario_actual] = lambda: self.vendedor

    def test_un_vendedor_no_puede_escribir_en_el_catalogo(self) -> None:
        libro = self._crear()  # como ADMIN
        self._como_vendedor()

        respuestas = {
            "alta": self.cliente.post("/libros/", json=_alta(isbn="978-950-00-0099-9")),
            "patch": self.cliente.patch(f"/libros/{libro['id']}", json={"titulo": "Nuevo"}),
            "baja": self.cliente.delete(f"/libros/{libro['id']}"),
            "reponer": self.cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 3}),
            "movimientos": self.cliente.get(f"/libros/{libro['id']}/movimientos"),
        }

        self.assertEqual({k: r.status_code for k, r in respuestas.items()},
                         {k: 403 for k in respuestas})
        filas = self._libros_en_tabla()
        self.assertEqual(len(filas), 1)
        self.assertEqual((filas[0].titulo, filas[0].stock), (libro["titulo"], 4))
        self.assertIsNone(filas[0].borrado_en)
        self.assertEqual(len(self._movimientos(libro["id"])), 1)

    def test_las_lecturas_del_catalogo_siguen_siendo_publicas(self) -> None:
        libro = self._crear()
        del app.dependency_overrides[get_usuario_actual]  # sin sesión

        self.assertEqual(self.cliente.get("/libros/").status_code, 200)
        self.assertEqual(self.cliente.get(f"/libros/{libro['id']}").status_code, 200)


if __name__ == "__main__":
    unittest.main()
