import asyncio
import math
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

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
from app.core.config import Settings
from app.core.security import hashear_password
from app.modules.usuarios.models import AsignacionRol, IntentoAcceso, Usuario


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


class TestAuthLoginService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _make_settings()
        self.hash_ficticio = await hashear_password("fake-password", self.settings)

    async def asyncTearDown(self):
        self.engine.dispose()

    def _create_uow_and_factory(self):
        from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork

        sync_session = Session(self.engine, expire_on_commit=False)
        adapter = _AsyncSessionAdapter(sync_session)
        uow = UsuarioUnitOfWork(adapter)

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def factory():
            with Session(self.engine, expire_on_commit=False) as s:
                yield _AsyncSessionAdapter(s)

        return uow, factory

    async def test_01_login_successful(self):
        from app.modules.usuarios.schemas import LoginRequest
        from app.modules.usuarios.service import login

        hashed = await hashear_password("ClaveSecreta123", self.settings)
        with Session(self.engine) as s:
            u = Usuario(
                email="admin@example.com",
                nombre="Admin",
                password_hash=hashed,
                activo=True,
            )
            s.add(u)
            s.commit()
            s.refresh(u)
            asig = AsignacionRol(usuario_id=u.id, rol="ADMIN")
            s.add(asig)
            s.commit()

        uow, factory = self._create_uow_and_factory()
        datos = LoginRequest(email="admin@example.com", password="ClaveSecreta123")
        usuario, token = await login(
            datos=datos,
            ip="127.0.0.1",
            uow=uow,
            session_factory=factory,
            settings=self.settings,
            hash_ficticio=self.hash_ficticio,
        )

        self.assertEqual(usuario.email, "admin@example.com")
        self.assertIsNotNone(token)

        # Intento anotado con exito=True
        with Session(self.engine) as s:
            intentos = list(s.exec(select(IntentoAcceso)).all())
            self.assertEqual(len(intentos), 1)
            self.assertTrue(intentos[0].exito)

    async def test_02_login_bad_password_raises_401_and_records_failure(self):
        from app.modules.usuarios.schemas import (
            CredencialesInvalidasError,
            LoginRequest,
        )
        from app.modules.usuarios.service import login

        hashed = await hashear_password("ClaveSecreta123", self.settings)
        with Session(self.engine) as s:
            u = Usuario(
                email="vendedor@example.com",
                nombre="Vendedor",
                password_hash=hashed,
                activo=True,
            )
            s.add(u)
            s.commit()

        uow, factory = self._create_uow_and_factory()
        datos = LoginRequest(email="vendedor@example.com", password="PasswordMala123")

        with self.assertRaises(CredencialesInvalidasError):
            await login(
                datos=datos,
                ip="127.0.0.1",
                uow=uow,
                session_factory=factory,
                settings=self.settings,
                hash_ficticio=self.hash_ficticio,
            )

        with Session(self.engine) as s:
            intentos = list(s.exec(select(IntentoAcceso)).all())
            self.assertEqual(len(intentos), 1)
            self.assertFalse(intentos[0].exito)

    async def test_03_login_nonexistent_user_uses_fake_hash_and_raises_401(self):
        from app.core.security import verificar_password
        from app.modules.usuarios.schemas import (
            CredencialesInvalidasError,
            LoginRequest,
        )
        from app.modules.usuarios.service import login

        uow, factory = self._create_uow_and_factory()
        datos = LoginRequest(email="inexistente@example.com", password="Password123")

        with patch("app.modules.usuarios.service.verificar_password", wraps=verificar_password) as spy_verif:
            with self.assertRaises(CredencialesInvalidasError):
                await login(
                    datos=datos,
                    ip="127.0.0.1",
                    uow=uow,
                    session_factory=factory,
                    settings=self.settings,
                    hash_ficticio=self.hash_ficticio,
                )
            # Debe haber verificado contra hash_ficticio
            self.assertEqual(spy_verif.call_count, 1)
            _, args, _ = spy_verif.mock_calls[0]
            self.assertEqual(args[1], self.hash_ficticio)

        with Session(self.engine) as s:
            intentos = list(s.exec(select(IntentoAcceso)).all())
            self.assertEqual(len(intentos), 1)
            self.assertFalse(intentos[0].exito)

    async def test_04_login_rate_limiting_after_5_failures_without_bcrypt(self):
        from app.modules.usuarios.schemas import (
            CredencialesInvalidasError,
            LimiteIntentosError,
            LoginRequest,
        )
        from app.modules.usuarios.service import login
        from app.modules.usuarios.unit_of_work import registrar_intento_acceso

        uow, factory = self._create_uow_and_factory()
        ahora = datetime.now(timezone.utc)

        # Insertar 5 fallos previos dentro de los 60s
        for i in range(5):
            await registrar_intento_acceso(
                factory,
                email="target@example.com",
                ip="192.168.1.50",
                exito=False,
                cuando=ahora - timedelta(seconds=40 - i * 5),
            )

        datos = LoginRequest(email="target@example.com", password="Password123")

        with patch("app.modules.usuarios.service.verificar_password") as spy_verif:
            with self.assertRaises(LimiteIntentosError) as ctx:
                await login(
                    datos=datos,
                    ip="192.168.1.50",
                    uow=uow,
                    session_factory=factory,
                    settings=self.settings,
                    hash_ficticio=self.hash_ficticio,
                )
            # El 6to intento no debió calcular hash alguno
            self.assertEqual(spy_verif.call_count, 0)
            self.assertGreater(ctx.exception.retry_after, 0)


if __name__ == "__main__":
    unittest.main()
