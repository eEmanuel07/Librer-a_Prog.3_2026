import unittest
from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.modules.autores.models  # noqa: F401
import app.modules.clientes.models  # noqa: F401
import app.modules.editoriales.models  # noqa: F401
import app.modules.generos.models  # noqa: F401
import app.modules.libros.models  # noqa: F401
import app.modules.ventas.models  # noqa: F401
from app.modules.usuarios.models import EventoSeguridad
from app.modules.usuarios.repository import EventoSeguridadRepository
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork


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


class TestAuthLogoutYoCambioUoW(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_usuario_uow_compone_evento_seguridad_repository(self):
        with Session(self.engine) as s:
            uow = UsuarioUnitOfWork(_AsyncSessionAdapter(s))
            self.assertTrue(hasattr(uow, "eventos"))
            self.assertIsInstance(uow.eventos, EventoSeguridadRepository)

    async def test_02_guardar_evento_seguridad_a_traves_de_uow(self):
        ahora = datetime.now(timezone.utc)
        with Session(self.engine) as s:
            uow = UsuarioUnitOfWork(_AsyncSessionAdapter(s))
            evento = EventoSeguridad(
                actor="test@example.com",
                accion="Cambio de contraseña",
                cuando=ahora,
            )
            await uow.eventos.add(evento)
            await uow.session.commit()

        with Session(self.engine) as s:
            guardado = s.exec(select(EventoSeguridad).where(EventoSeguridad.actor == "test@example.com")).first()
            self.assertIsNotNone(guardado)
            self.assertEqual(guardado.accion, "Cambio de contraseña")


if __name__ == "__main__":
    unittest.main()
