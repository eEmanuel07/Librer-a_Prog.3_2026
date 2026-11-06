import asyncio
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.modules.autores.models  # noqa: F401
import app.modules.clientes.models  # noqa: F401
import app.modules.editoriales.models  # noqa: F401
import app.modules.generos.models  # noqa: F401
import app.modules.libros.models  # noqa: F401
import app.modules.ventas.models  # noqa: F401
from app.core.config import Settings
from app.core.errors import Conflicto
from app.core.security import verificar_password
from app.modules.clientes.models import Cliente
from app.modules.clientes.repository import ClienteRepository
from app.modules.usuarios.models import AsignacionRol, Usuario
from app.modules.usuarios.schemas import RegistroRequest
from app.modules.usuarios.service import registrar
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork


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


class TestAuthRegistroService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _make_settings()

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_usuario_uow_compone_cliente_repository(self):
        with Session(self.engine) as s:
            uow = UsuarioUnitOfWork(_AsyncSessionAdapter(s))
            self.assertTrue(hasattr(uow, "clientes"))
            self.assertIsInstance(uow.clientes, ClienteRepository)

    async def test_02_registrar_usuario_rol_y_cliente_exitoso(self):
        datos = RegistroRequest(
            nombre="Juan Pérez",
            email="juan.perez@example.com",
            password="MiPassword123!",
        )

        with Session(self.engine) as s:
            uow = UsuarioUnitOfWork(_AsyncSessionAdapter(s))
            res = await registrar(datos, uow, self.settings)

            self.assertEqual(res.nombre, "Juan Pérez")
            self.assertEqual(res.email, "juan.perez@example.com")
            self.assertIsInstance(res.id, int)
            self.assertIsInstance(res.cliente_id, int)
            self.assertEqual(res.mensaje, "Usuario registrado exitosamente")

        # Verificar en base que están las 3 filas
        with Session(self.engine) as s:
            user = s.exec(select(Usuario).where(Usuario.email == "juan.perez@example.com")).first()
            self.assertIsNotNone(user)
            self.assertEqual(user.nombre, "Juan Pérez")
            self.assertTrue(user.activo)
            self.assertFalse(user.debe_cambiar_password)
            # Contraseña hasheada con bcrypt
            es_valido = await verificar_password("MiPassword123!", user.password_hash, settings=self.settings)
            self.assertTrue(es_valido)

            # Rol CLIENTE
            asig = s.exec(select(AsignacionRol).where(AsignacionRol.usuario_id == user.id)).first()
            self.assertIsNotNone(asig)
            self.assertEqual(asig.rol, "CLIENTE")

            # Ficha Cliente
            cliente = s.exec(select(Cliente).where(Cliente.email == "juan.perez@example.com")).first()
            self.assertIsNotNone(cliente)
            self.assertEqual(cliente.nombre, "Juan Pérez")
            self.assertEqual(cliente.usuario_id, user.id)

    async def test_03_registrar_correo_duplicado_en_usuario_lanza_conflicto_y_revierte(self):
        # Insertar usuario previo
        with Session(self.engine) as s:
            u = Usuario(
                nombre="Existente",
                email="repetido@example.com",
                password_hash="fakehash",
                activo=True,
            )
            s.add(u)
            s.commit()

        datos = RegistroRequest(
            nombre="Nuevo Intentando Mismo Email",
            email="repetido@example.com",
            password="Password123!",
        )

        with Session(self.engine) as s:
            uow = UsuarioUnitOfWork(_AsyncSessionAdapter(s))
            with self.assertRaises(Conflicto):
                await registrar(datos, uow, self.settings)

        # Comprobar que no se creó cliente ni asignación rol
        with Session(self.engine) as s:
            cl = s.exec(select(Cliente).where(Cliente.email == "repetido@example.com")).first()
            self.assertIsNone(cl)

    async def test_04_registrar_correo_duplicado_en_cliente_lanza_conflicto_y_no_se_apropia(self):
        # Insertar cliente previo sin usuario
        with Session(self.engine) as s:
            cliente_previo = Cliente(
                nombre="Cliente Físico Preexistente",
                email="cliente.mostrador@example.com",
                usuario_id=None,
            )
            s.add(cliente_previo)
            s.commit()
            s.refresh(cliente_previo)
            cliente_id_original = cliente_previo.id

        datos = RegistroRequest(
            nombre="Alguien Con Mismo Email",
            email="cliente.mostrador@example.com",
            password="Password123!",
        )

        with Session(self.engine) as s:
            uow = UsuarioUnitOfWork(_AsyncSessionAdapter(s))
            with self.assertRaises(Conflicto):
                await registrar(datos, uow, self.settings)

        # Comprobar que:
        # 1. No se creó Usuario
        # 2. No se creó AsignacionRol
        # 3. El cliente preexistente sigue intacto con usuario_id en None (no se apropia de la ficha)
        with Session(self.engine) as s:
            u = s.exec(select(Usuario).where(Usuario.email == "cliente.mostrador@example.com")).first()
            self.assertIsNone(u)

            cl = s.exec(select(Cliente).where(Cliente.id == cliente_id_original)).first()
            self.assertIsNotNone(cl)
            self.assertIsNone(cl.usuario_id)
            self.assertEqual(cl.nombre, "Cliente Físico Preexistente")


if __name__ == "__main__":
    unittest.main()
