from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings
from app.core.database import crear_fabrica_sesiones, crear_motor, get_session
from app.main import lifespan
from app.modules.health import router as health_router_module
from app.modules.health.router import router as health_router


def _crear_settings(**overrides) -> Settings:
    valores = {
        "postgres_user": "postgres",
        "postgres_password": "secret-db-password",
        "postgres_db": "libreria",
        "postgres_host": "localhost",
        "postgres_port": 5433,
        "db_pool_size": 7,
        "db_max_overflow": 14,
        "sql_echo": False,
        "jwt_secret": "a" * 32,
        "jwt_expira_minutos": 30,
        "cookie_secure": False,
        "bcrypt_costo": 4,
        "bcrypt_concurrencia": 2,
    }
    valores.update(overrides)
    return Settings(**valores)


class _SesionSaludFalsa:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.consultas: list[str] = []

    async def execute(self, statement) -> None:
        self.consultas.append(str(statement))
        if self.error is not None:
            raise self.error


class TestMotorYLifespan(unittest.IsolatedAsyncioTestCase):
    async def test_01_crear_motor_aplica_pool_size_y_max_overflow_personalizados(self) -> None:
        motor = crear_motor(
            "postgresql+asyncpg://postgres:secreto@localhost:5433/libreria",
            echo=True,
            pool_size=8,
            max_overflow=15,
        )
        try:
            self.assertEqual(motor.pool.size(), 8)
            self.assertEqual(motor.pool._max_overflow, 15)
            self.assertTrue(motor.echo)
        finally:
            await motor.dispose()

    async def test_02_crear_motor_usa_valores_por_defecto_del_pool(self) -> None:
        with patch("app.core.database.create_async_engine") as mock_create_engine:
            crear_motor("postgresql+asyncpg://postgres:secreto@localhost:5433/libreria")
            mock_create_engine.assert_called_once_with(
                "postgresql+asyncpg://postgres:secreto@localhost:5433/libreria",
                echo=False,
                pool_size=5,
                max_overflow=10,
            )

    async def test_03_crear_fabrica_sesiones_configura_expire_on_commit_false(self) -> None:
        motor = crear_motor("postgresql+asyncpg://postgres:secreto@localhost:5433/libreria")
        try:
            fabrica = crear_fabrica_sesiones(motor)
            self.assertIs(fabrica.kw.get("expire_on_commit"), False)
            self.assertIs(fabrica.class_, AsyncSession)
        finally:
            await motor.dispose()

    async def test_04_lifespan_crea_recursos_con_el_pool_de_settings_y_hace_dispose(self) -> None:
        settings = _crear_settings(db_pool_size=7, db_max_overflow=14, sql_echo=True)
        app_prueba = FastAPI()

        motor_real = crear_motor(settings.database_url, echo=settings.sql_echo)
        try:
            with (
                patch("app.main.get_settings", return_value=settings),
                patch("app.main.crear_motor", return_value=motor_real) as mock_crear_motor,
                patch.object(
                    type(motor_real),
                    "dispose",
                    new_callable=AsyncMock,
                ) as mock_dispose,
            ):
                async with lifespan(app_prueba):
                    mock_crear_motor.assert_called_once_with(
                        settings.database_url,
                        echo=settings.sql_echo,
                        pool_size=7,
                        max_overflow=14,
                    )
                    self.assertIs(app_prueba.state.settings, settings)
                    self.assertIs(app_prueba.state.engine, motor_real)
                    self.assertIsNotNone(app_prueba.state.session_factory)
                    self.assertIs(
                        app_prueba.state.session_factory.kw.get("expire_on_commit"),
                        False,
                    )
                    self.assertTrue(
                        isinstance(app_prueba.state.hash_ficticio, str)
                        and app_prueba.state.hash_ficticio.startswith("$2b$")
                    )
                    mock_dispose.assert_not_awaited()

                mock_dispose.assert_awaited_once()
        finally:
            await motor_real.dispose()


class TestHealthRouter(unittest.IsolatedAsyncioTestCase):
    def _armar_cliente(self, sesion: _SesionSaludFalsa) -> tuple[TestClient, list[int]]:
        app_prueba = FastAPI()
        app_prueba.include_router(health_router)
        aperturas_sesion: list[int] = []

        async def override_get_session():
            aperturas_sesion.append(1)
            yield sesion

        app_prueba.dependency_overrides[get_session] = override_get_session
        return TestClient(app_prueba), aperturas_sesion

    def test_01_modulo_health_solo_tiene_router_py_sin_service_py(self) -> None:
        carpeta_health = Path(health_router_module.__file__).resolve().parent
        self.assertFalse(
            (carpeta_health / "service.py").exists(),
            "El módulo health sólo debe tener router.py (estructura obligatoria, pág. 8).",
        )
        self.assertFalse(
            hasattr(health_router_module, "service"),
            "app/modules/health/router.py no debe importar ni delegar en service.py.",
        )

    def test_02_con_base_arriba_live_y_ready_responden_200(self) -> None:
        sesion = _SesionSaludFalsa()
        cliente, aperturas = self._armar_cliente(sesion)

        r_live = cliente.get("/health/live")
        self.assertEqual(r_live.status_code, 200)
        self.assertEqual(r_live.json(), {"estado": "vivo"})
        self.assertEqual(len(aperturas), 0)
        self.assertEqual(sesion.consultas, [])

        r_ready = cliente.get("/health/ready")
        self.assertEqual(r_ready.status_code, 200)
        self.assertEqual(r_ready.json(), {"estado": "listo", "base": "ok"})
        self.assertEqual(len(aperturas), 1)
        self.assertEqual(sesion.consultas, ["SELECT 1"])

    def test_03_con_base_caida_sqlalchemy_ready_da_503_sin_texto_interno_y_live_da_200(
        self,
    ) -> None:
        error_interno = OperationalError(
            "SELECT 1",
            {},
            Exception("FATAL: database 'libreria' does not exist on port 5433"),
        )
        sesion = _SesionSaludFalsa(error=error_interno)
        cliente, aperturas = self._armar_cliente(sesion)

        r_ready = cliente.get("/health/ready")
        self.assertEqual(r_ready.status_code, 503)
        self.assertEqual(
            r_ready.json(),
            {"detail": "La base de datos no está disponible"},
        )
        cuerpo = r_ready.text
        self.assertNotIn("FATAL", cuerpo)
        self.assertNotIn("5433", cuerpo)
        self.assertNotIn("SELECT 1", cuerpo)
        self.assertEqual(len(aperturas), 1)

        r_live = cliente.get("/health/live")
        self.assertEqual(r_live.status_code, 200)
        self.assertEqual(r_live.json(), {"estado": "vivo"})
        self.assertEqual(len(aperturas), 1)

    def test_04_con_base_caida_oserror_ready_da_503_sin_texto_interno_y_live_da_200(
        self,
    ) -> None:
        sesion = _SesionSaludFalsa(
            error=OSError("Multiple exceptions: [Errno 111] Connect call failed ('127.0.0.1', 5999)")
        )
        cliente, aperturas = self._armar_cliente(sesion)

        r_ready = cliente.get("/health/ready")
        self.assertEqual(r_ready.status_code, 503)
        self.assertEqual(
            r_ready.json(),
            {"detail": "La base de datos no está disponible"},
        )
        self.assertNotIn("5999", r_ready.text)
        self.assertNotIn("Connect call failed", r_ready.text)
        self.assertEqual(len(aperturas), 1)

        r_live = cliente.get("/health/live")
        self.assertEqual(r_live.status_code, 200)
        self.assertEqual(r_live.json(), {"estado": "vivo"})
        self.assertEqual(len(aperturas), 1)
