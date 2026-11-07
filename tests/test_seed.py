from decimal import Decimal
from pathlib import Path
import unittest

from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.core.config import Settings
from app.modules.autores.models import Autor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor, MovimientoStock
from app.modules.libros.repository import LibroRepository
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, IntentoAcceso, Usuario
from app.modules.ventas.models import RenglonVenta, Venta

_MODELOS = (
    Editorial,
    Genero,
    Autor,
    Libro,
    LibroAutor,
    MovimientoStock,
    Cliente,
    PerfilCliente,
    Venta,
    RenglonVenta,
    Usuario,
    AsignacionRol,
    IntentoAcceso,
    EventoSeguridad,
)


def _settings_prueba() -> Settings:
    return Settings(
        postgres_password="test-password",
        jwt_secret="x" * 32,
        bcrypt_costo=4,
        bcrypt_concurrencia=2,
    )


class _ConexionAdapter:
    def __init__(self, sync_session: Session) -> None:
        self._s = sync_session
        self.dialect = sync_session.bind.dialect

    async def execute(self, statement):
        return self._s.execute(statement)


class _AsyncSessionAdapter:
    def __init__(self, sync_session: Session) -> None:
        self._s = sync_session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._s.close()

    def add(self, obj) -> None:
        self._s.add(obj)

    def add_all(self, objs) -> None:
        self._s.add_all(objs)

    async def flush(self) -> None:
        self._s.flush()

    async def commit(self) -> None:
        self._s.commit()

    async def rollback(self) -> None:
        self._s.rollback()

    async def exec(self, statement):
        return self._s.exec(statement)

    async def connection(self) -> _ConexionAdapter:
        return _ConexionAdapter(self._s)


class SeedTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _settings_prueba()

        def fabrica() -> _AsyncSessionAdapter:
            return _AsyncSessionAdapter(Session(self.engine, expire_on_commit=False))

        self.fabrica = fabrica

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_seed_existe_en_la_raiz_y_no_en_scripts(self) -> None:
        raiz = Path(__file__).resolve().parent.parent
        self.assertTrue((raiz / "seed.py").is_file())
        self.assertFalse((raiz / "scripts" / "seed.py").exists())

    async def test_sembrar_carga_datos_cumple_invariante_y_es_idempotente(self) -> None:
        import seed

        await seed.sembrar(fabrica=self.fabrica, settings=self.settings)
        # Correrlo por segunda vez debe vaciar las tablas y producir el mismo estado
        await seed.sembrar(fabrica=self.fabrica, settings=self.settings)

        async with self.fabrica() as session:
            usuarios = (await session.exec(select(Usuario).order_by(Usuario.id))).all()
            self.assertEqual(len(usuarios), 5)
            por_email = {u.email: u for u in usuarios}
            self.assertEqual(
                set(por_email.keys()),
                {
                    "admin@example.com",
                    "admin2@example.com",
                    "vendedor@example.com",
                    "ana@example.com",
                    "nuevo@example.com",
                },
            )
            self.assertFalse(por_email["admin@example.com"].debe_cambiar_password)
            self.assertFalse(por_email["admin2@example.com"].debe_cambiar_password)
            self.assertFalse(por_email["vendedor@example.com"].debe_cambiar_password)
            self.assertFalse(por_email["ana@example.com"].debe_cambiar_password)
            self.assertTrue(por_email["nuevo@example.com"].debe_cambiar_password)

            asignaciones = (await session.exec(select(AsignacionRol))).all()
            roles_por_usuario = {a.usuario_id: a.rol for a in asignaciones}
            self.assertEqual(roles_por_usuario[por_email["admin@example.com"].id], "ADMIN")
            self.assertEqual(roles_por_usuario[por_email["admin2@example.com"].id], "ADMIN")
            self.assertEqual(roles_por_usuario[por_email["vendedor@example.com"].id], "VENDEDOR")
            self.assertEqual(roles_por_usuario[por_email["ana@example.com"].id], "CLIENTE")
            self.assertEqual(roles_por_usuario[por_email["nuevo@example.com"].id], "VENDEDOR")

            editoriales = (await session.exec(select(Editorial))).all()
            generos = (await session.exec(select(Genero))).all()
            autores = (await session.exec(select(Autor))).all()
            self.assertEqual(len(editoriales), 3)
            self.assertEqual(len(generos), 3)
            self.assertEqual(len(autores), 6)

            libros = (await session.exec(select(Libro).order_by(Libro.id))).all()
            self.assertEqual(len(libros), 5)
            stocks = {libro.titulo: libro.stock for libro in libros}
            self.assertEqual(
                stocks,
                {
                    "Rayuela": 10,
                    "Antología de la literatura fantástica": 5,
                    "Ficciones": 8,
                    "Respiración artificial": 3,
                    "Bestiario": 1,
                },
            )

            # Invariante RN-11: para los cinco libros, stock = suma de movimientos
            repo_libros = LibroRepository(session)
            self.assertEqual(await repo_libros.ids_con_stock_inconsistente(), [])

            movimientos = (await session.exec(select(MovimientoStock))).all()
            self.assertEqual(len(movimientos), 7)

            clientes = (await session.exec(select(Cliente).order_by(Cliente.id))).all()
            self.assertEqual(len(clientes), 3)
            clientes_por_email = {c.email: c for c in clientes}
            self.assertIsNone(clientes_por_email["lucia@example.com"].usuario_id)
            self.assertIsNone(clientes_por_email["tomas@example.com"].usuario_id)
            self.assertEqual(
                clientes_por_email["ana@example.com"].usuario_id,
                por_email["ana@example.com"].id,
            )

            perfiles = (await session.exec(select(PerfilCliente))).all()
            self.assertEqual(len(perfiles), 1)
            self.assertEqual(perfiles[0].cliente_id, clientes_por_email["lucia@example.com"].id)

            ventas = (await session.exec(select(Venta))).all()
            self.assertEqual(len(ventas), 1)
            self.assertEqual(ventas[0].cliente_id, clientes_por_email["lucia@example.com"].id)
            self.assertEqual(ventas[0].total, Decimal("69000.00"))

            renglones = (await session.exec(select(RenglonVenta))).all()
            self.assertEqual(len(renglones), 2)

            eventos = (await session.exec(select(EventoSeguridad))).all()
            self.assertEqual(len(eventos), 1)
            self.assertEqual(eventos[0].actor, "SISTEMA")
            self.assertEqual(eventos[0].accion, "Carga de los datos iniciales")
