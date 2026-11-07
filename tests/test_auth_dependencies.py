import unittest
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI
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
from app.core.dependencies import get_usuario_actual, requiere_rol
from app.core.security import crear_access_token
from app.modules.editoriales.unit_of_work import EditorialUnitOfWork, get_editoriales_uow
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


class TestAuthDependencies(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _make_settings()

        self.app = FastAPI()

        @self.app.get("/ruta-protegida")
        async def ruta_protegida(usuario: Usuario = Depends(get_usuario_actual)):
            return {"id": usuario.id, "email": usuario.email}

        async def override_get_session():
            with Session(self.engine, expire_on_commit=False) as s:
                yield _AsyncSessionAdapter(s)

        self.app.dependency_overrides[get_session] = override_get_session
        self.app.dependency_overrides[get_settings] = lambda: self.settings

        self.client = TestClient(self.app)

    async def asyncTearDown(self):
        self.engine.dispose()

    async def test_01_sin_cookie_retorna_401(self):
        resp = self.client.get("/ruta-protegida")
        self.assertEqual(resp.status_code, 401)

    async def test_02_token_invalido_retorna_401(self):
        resp = self.client.get("/ruta-protegida", cookies={"access_token": "token-basura"})
        self.assertEqual(resp.status_code, 401)

    async def test_03_token_vencido_retorna_401(self):
        hace_una_hora = datetime.now(timezone.utc) - timedelta(hours=1)
        token_vencido = crear_access_token(1, ["CLIENTE"], settings=self.settings, ahora=hace_una_hora)
        resp = self.client.get("/ruta-protegida", cookies={"access_token": token_vencido})
        self.assertEqual(resp.status_code, 401)

    async def test_04_usuario_inexistente_en_base_retorna_401(self):
        token = crear_access_token(999, ["CLIENTE"], settings=self.settings)
        resp = self.client.get("/ruta-protegida", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 401)

    async def test_05_usuario_inactivo_retorna_401(self):
        with Session(self.engine) as s:
            u = Usuario(
                id=2,
                nombre="Inactivo",
                email="inactivo@example.com",
                password_hash="fakehash",
                activo=False,
            )
            s.add(u)
            s.commit()

        token = crear_access_token(2, ["CLIENTE"], settings=self.settings)
        resp = self.client.get("/ruta-protegida", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 401)

    async def test_06_usuario_activo_autentica_exitosamente(self):
        with Session(self.engine) as s:
            u = Usuario(
                id=1,
                nombre="Usuario Valido",
                email="valido@example.com",
                password_hash="fakehash",
                activo=True,
            )
            s.add(u)
            s.commit()

        token = crear_access_token(1, ["CLIENTE"], settings=self.settings)
        resp = self.client.get("/ruta-protegida", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"id": 1, "email": "valido@example.com"})


class TestRequiereRol(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.settings = _make_settings()
        self.sesiones_abiertas: list[_AsyncSessionAdapter] = []

        self.app = FastAPI()

        @self.app.get("/solo-admin")
        async def ruta_admin(
            usuario: Usuario = Depends(requiere_rol("ADMIN")),
            uow: EditorialUnitOfWork = Depends(get_editoriales_uow),
        ):
            return {
                "id": usuario.id,
                "email": usuario.email,
                "misma_sesion": uow.session in self.sesiones_abiertas,
            }

        @self.app.get("/personal")
        async def ruta_personal(
            usuario: Usuario = Depends(requiere_rol("VENDEDOR", "ADMIN")),
        ):
            return {"id": usuario.id, "email": usuario.email}

        async def override_get_session():
            with Session(self.engine, expire_on_commit=False) as s:
                adaptador = _AsyncSessionAdapter(s)
                self.sesiones_abiertas.append(adaptador)
                yield adaptador

        self.app.dependency_overrides[get_session] = override_get_session
        self.app.dependency_overrides[get_settings] = lambda: self.settings

        self.client = TestClient(self.app)

    async def asyncTearDown(self):
        self.engine.dispose()

    def _crear_usuario_con_rol(
        self,
        usuario_id: int,
        email: str,
        rol: str | None = None,
        vence_en: datetime | None = None,
        revocada_en: datetime | None = None,
    ) -> None:
        with Session(self.engine) as s:
            u = Usuario(
                id=usuario_id,
                nombre=f"Usuario {usuario_id}",
                email=email,
                password_hash="fakehash",
                activo=True,
            )
            s.add(u)
            s.commit()
            if rol is not None:
                s.add(
                    AsignacionRol(
                        usuario_id=usuario_id,
                        rol=rol,
                        vence_en=vence_en,
                        revocada_en=revocada_en,
                    )
                )
                s.commit()

    async def test_01_usuario_con_rol_vigente_retorna_200_y_comparte_sesion_con_uow(self):
        self._crear_usuario_con_rol(1, "admin@example.com", rol="ADMIN")
        token = crear_access_token(1, ["ADMIN"], settings=self.settings)

        resp = self.client.get("/solo-admin", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {"id": 1, "email": "admin@example.com", "misma_sesion": True},
        )
        # get_usuario_actual, requiere_rol y el UoW compartieron una sola sesión
        self.assertEqual(len(self.sesiones_abiertas), 1)

    async def test_02_c06_usuario_sin_el_rol_requerido_retorna_403(self):
        self._crear_usuario_con_rol(2, "vendedor@example.com", rol="VENDEDOR")
        # Aunque el token diga ADMIN, manda la base (RN-04)
        token = crear_access_token(2, ["ADMIN", "VENDEDOR"], settings=self.settings)

        resp = self.client.get("/solo-admin", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 403)

    async def test_03_c07_revocar_rol_con_sesion_abierta_da_403_en_la_peticion_siguiente(self):
        self._crear_usuario_con_rol(3, "admin2@example.com", rol="ADMIN")
        token = crear_access_token(3, ["ADMIN"], settings=self.settings)

        # Primera petición: el rol está vigente -> 200
        resp1 = self.client.get("/solo-admin", cookies={"access_token": token})
        self.assertEqual(resp1.status_code, 200)

        # Se revoca el rol en la base mientras la sesión sigue abierta
        with Session(self.engine) as s:
            asignacion = s.get(AsignacionRol, 1)
            asignacion.revocada_en = datetime.now(timezone.utc)
            s.add(asignacion)
            s.commit()

        # Petición siguiente con la misma cookie: 403 (C-07)
        resp2 = self.client.get("/solo-admin", cookies={"access_token": token})
        self.assertEqual(resp2.status_code, 403)

    async def test_04_rol_vencido_en_la_base_retorna_403_aunque_token_siga_vigente(self):
        ayer = datetime.now(timezone.utc) - timedelta(days=1)
        self._crear_usuario_con_rol(4, "vencido@example.com", rol="ADMIN", vence_en=ayer)
        token = crear_access_token(4, ["ADMIN"], settings=self.settings)

        resp = self.client.get("/solo-admin", cookies={"access_token": token})
        self.assertEqual(resp.status_code, 403)

    async def test_05_multiples_roles_permite_cualquiera_de_los_indicados_y_rechaza_otro(self):
        self._crear_usuario_con_rol(10, "vendedor@example.com", rol="VENDEDOR")
        self._crear_usuario_con_rol(11, "admin@example.com", rol="ADMIN")
        self._crear_usuario_con_rol(12, "cliente@example.com", rol="CLIENTE")

        t_vendedor = crear_access_token(10, ["VENDEDOR"], settings=self.settings)
        t_admin = crear_access_token(11, ["ADMIN"], settings=self.settings)
        t_cliente = crear_access_token(12, ["CLIENTE"], settings=self.settings)

        self.assertEqual(
            self.client.get("/personal", cookies={"access_token": t_vendedor}).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/personal", cookies={"access_token": t_admin}).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/personal", cookies={"access_token": t_cliente}).status_code,
            403,
        )

    def test_06_requiere_rol_sin_roles_lanza_value_error(self):
        with self.assertRaises(ValueError):
            requiere_rol()


if __name__ == "__main__":
    unittest.main()
