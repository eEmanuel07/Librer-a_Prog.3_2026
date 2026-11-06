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
from app.core.config import Settings
from app.core.security import hashear_password, verificar_password
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from app.modules.usuarios.schemas import (
    CambioPasswordRequest,
    CredencialesInvalidasError,
    YoResponse,
)
from app.modules.usuarios.service import cambiar_password, obtener_yo
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


class TestAuthLogoutYoCambioService(unittest.IsolatedAsyncioTestCase):
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

    async def test_01_obtener_yo_devuelve_roles_vigentes_y_roles_token(self):
        with Session(self.engine) as s:
            u = Usuario(
                id=1,
                nombre="Carlos",
                email="carlos@example.com",
                password_hash="hash",
                activo=True,
                debe_cambiar_password=True,
            )
            s.add(u)
            s.commit()
            s.add(AsignacionRol(usuario_id=1, rol="ADMIN"))
            s.add(AsignacionRol(usuario_id=1, rol="VENDEDOR"))
            s.commit()

        with Session(self.engine) as s:
            uow = UsuarioUnitOfWork(_AsyncSessionAdapter(s))
            user = s.get(Usuario, 1)
            resp = await obtener_yo(usuario=user, roles_token=["ADMIN"], uow=uow)

            self.assertIsInstance(resp, YoResponse)
            self.assertEqual(resp.id, 1)
            self.assertEqual(resp.email, "carlos@example.com")
            self.assertEqual(resp.nombre, "Carlos")
            self.assertTrue(resp.debe_cambiar_password)
            self.assertEqual(sorted(resp.roles), ["ADMIN", "VENDEDOR"])
            self.assertEqual(resp.roles_token, ["ADMIN"])

    async def test_02_cambiar_password_exitoso_actualiza_hash_desmarca_flag_y_crea_evento(self):
        hash_inicial = await hashear_password("PasswordVieja123!", settings=self.settings)
        with Session(self.engine) as s:
            u = Usuario(
                id=5,
                nombre="Elena",
                email="elena@example.com",
                password_hash=hash_inicial,
                activo=True,
                debe_cambiar_password=True,
            )
            s.add(u)
            s.commit()

        datos = CambioPasswordRequest(
            password_actual="PasswordVieja123!",
            password_nueva="PasswordNueva456!",
        )

        with Session(self.engine) as s:
            uow = UsuarioUnitOfWork(_AsyncSessionAdapter(s))
            user = s.get(Usuario, 5)
            resp = await cambiar_password(datos=datos, usuario=user, uow=uow, settings=self.settings)
            self.assertEqual(resp.mensaje, "Contraseña actualizada exitosamente")

        # Verificar en base de datos
        with Session(self.engine) as s:
            actualizado = s.get(Usuario, 5)
            self.assertFalse(actualizado.debe_cambiar_password)
            # La nueva contraseña debe ser válida
            es_valida = await verificar_password("PasswordNueva456!", actualizado.password_hash, settings=self.settings)
            self.assertTrue(es_valida)
            # La vieja ya no debe coincidir
            es_vieja_valida = await verificar_password("PasswordVieja123!", actualizado.password_hash, settings=self.settings)
            self.assertFalse(es_vieja_valida)

            # Verificar EventoSeguridad (RN-16)
            eventos = s.exec(select(EventoSeguridad).where(EventoSeguridad.actor == "elena@example.com")).all()
            self.assertEqual(len(eventos), 1)
            self.assertEqual(eventos[0].accion, "Cambio de contraseña")
            self.assertIsNotNone(eventos[0].cuando)

    async def test_03_cambiar_password_clave_actual_incorrecta_lanza_error_y_no_cambia(self):
        hash_inicial = await hashear_password("PasswordCorrecta123!", settings=self.settings)
        with Session(self.engine) as s:
            u = Usuario(
                id=6,
                nombre="Mario",
                email="mario@example.com",
                password_hash=hash_inicial,
                activo=True,
                debe_cambiar_password=True,
            )
            s.add(u)
            s.commit()

        datos = CambioPasswordRequest(
            password_actual="ClaveErronea123!",
            password_nueva="PasswordNueva456!",
        )

        with Session(self.engine) as s:
            uow = UsuarioUnitOfWork(_AsyncSessionAdapter(s))
            user = s.get(Usuario, 6)
            with self.assertRaises(CredencialesInvalidasError):
                await cambiar_password(datos=datos, usuario=user, uow=uow, settings=self.settings)

        # Verificar en base que no cambió nada
        with Session(self.engine) as s:
            intacto = s.get(Usuario, 6)
            self.assertEqual(intacto.password_hash, hash_inicial)
            self.assertTrue(intacto.debe_cambiar_password)
            eventos = s.exec(select(EventoSeguridad).where(EventoSeguridad.actor == "mario@example.com")).all()
            self.assertEqual(len(eventos), 0)


if __name__ == "__main__":
    unittest.main()
