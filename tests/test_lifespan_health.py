import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.main import lifespan


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
