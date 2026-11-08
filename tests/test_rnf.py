"""Tests de verificación de Requisitos No Funcionales (RNF) — [H8] (#44).

Comprueba programáticamente las invariantes transversales exigidas en las
páginas 20-21 de la consigna y en knowledge-base/05_reglas_de_negocio.md:
1. Sin secretos ni contraseñas por defecto en Settings, alembic.ini ni repo.
2. Prohibición de carga perezosa: todas las relaciones SQLModel usan lazy="raise".
3. Disciplina transaccional: ningún repositorio llama a commit() y ningún
   servicio instancia su propio UnitOfWork.
4. Contratos estrictos (RN-15): todos los DTOs de entrada usan extra="forbid".
5. Token exclusivamente en cookie HttpOnly (nunca en body ni header Authorization).
6. Consistencia de archivos .http en test/ (sintaxis $.id, paginación page/size
   y sesión ADMIN en escrituras de catálogo protegidas por R7).
"""

import ast
import inspect
import re
import unittest
from pathlib import Path

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import class_mapper

import app.modules.autores.models
import app.modules.autores.repository
import app.modules.autores.schemas
import app.modules.autores.service
import app.modules.clientes.models
import app.modules.clientes.repository
import app.modules.clientes.schemas
import app.modules.clientes.service
import app.modules.editoriales.models
import app.modules.editoriales.repository
import app.modules.editoriales.schemas
import app.modules.editoriales.service
import app.modules.generos.models
import app.modules.generos.repository
import app.modules.generos.schemas
import app.modules.generos.service
import app.modules.libros.models
import app.modules.libros.repository
import app.modules.libros.schemas
import app.modules.libros.service
import app.modules.usuarios.models
import app.modules.usuarios.repository
import app.modules.usuarios.schemas
import app.modules.usuarios.service
import app.modules.ventas.models
import app.modules.ventas.repository
import app.modules.ventas.schemas
import app.modules.ventas.service
from app.core.config import Settings
from app.core.errors import conflicto_por_integridad
from app.core.repository import BaseRepository, SoftDeleteRepository

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestCredencialesYSecretosRNF(unittest.TestCase):
    """RNF 1: Ninguna contraseña ni clave de firma por defecto ni en archivos de config."""

    def test_01_settings_exige_postgres_password_y_jwt_secret_sin_defaults(self) -> None:
        campos = Settings.model_fields
        self.assertTrue(campos["postgres_password"].is_required())
        self.assertTrue(campos["jwt_secret"].is_required())

        with self.assertRaises(ValidationError):
            Settings(_env_file=None)  # type: ignore[call-arg]

    def test_02_database_url_no_se_expone_en_repr(self) -> None:
        s = Settings(
            _env_file=None,
            postgres_password="clave-super-secreta",
            jwt_secret="x" * 32,
        )
        representacion = repr(s)
        self.assertNotIn("clave-super-secreta", representacion)
        self.assertNotIn("x" * 32, representacion)

    def test_03_alembic_ini_y_env_example_no_tienen_secretos(self) -> None:
        alembic_ini = (ROOT_DIR / "alembic.ini").read_text(encoding="utf-8")
        for linea in alembic_ini.splitlines():
            limpia = linea.strip()
            if limpia and not limpia.startswith("#"):
                self.assertFalse(
                    limpia.startswith("sqlalchemy.url"),
                    f"alembic.ini no debe definir sqlalchemy.url: {limpia}",
                )

        env_example = (ROOT_DIR / "env.example").read_text(encoding="utf-8")
        self.assertIn("POSTGRES_PASSWORD=\n", env_example)
        self.assertIn("JWT_SECRET=\n", env_example)


class TestLazyRaiseYTransaccionesRNF(unittest.TestCase):
    """RNF 2 y 3: Prohibición de carga perezosa y disciplina transaccional."""

    def test_01_todas_las_relaciones_sqlmodel_declaran_lazy_raise(self) -> None:
        modulos_modelos = [
            app.modules.autores.models,
            app.modules.clientes.models,
            app.modules.editoriales.models,
            app.modules.generos.models,
            app.modules.libros.models,
            app.modules.usuarios.models,
            app.modules.ventas.models,
        ]
        relaciones_auditadas = 0
        for mod in modulos_modelos:
            for _, cls in inspect.getmembers(mod, inspect.isclass):
                if getattr(cls, "__table__", None) is None:
                    continue
                mapper = class_mapper(cls)
                for rel in mapper.relationships:
                    relaciones_auditadas += 1
                    self.assertEqual(
                        rel.lazy,
                        "raise",
                        f"La relación {cls.__name__}.{rel.key} tiene lazy={rel.lazy!r} en vez de 'raise'",
                    )
        self.assertGreaterEqual(relaciones_auditadas, 20)

    def test_02_ningun_repositorio_llama_a_commit(self) -> None:
        modulos_repos = [
            app.core.repository,
            app.modules.autores.repository,
            app.modules.clientes.repository,
            app.modules.editoriales.repository,
            app.modules.generos.repository,
            app.modules.libros.repository,
            app.modules.usuarios.repository,
            app.modules.ventas.repository,
        ]
        for mod in modulos_repos:
            fuente = inspect.getsource(mod)
            arbol = ast.parse(fuente)
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                    self.assertNotEqual(
                        nodo.func.attr,
                        "commit",
                        f"El módulo de repositorio {mod.__name__} invoca .commit()",
                    )

    def test_03_ningun_servicio_instancia_unit_of_work(self) -> None:
        modulos_servicios = [
            app.modules.autores.service,
            app.modules.clientes.service,
            app.modules.editoriales.service,
            app.modules.generos.service,
            app.modules.libros.service,
            app.modules.usuarios.service,
            app.modules.ventas.service,
        ]
        for mod in modulos_servicios:
            fuente = inspect.getsource(mod)
            arbol = ast.parse(fuente)
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                    self.assertFalse(
                        nodo.func.id.endswith("UnitOfWork"),
                        f"El servicio {mod.__name__} construye {nodo.func.id} directamente",
                    )


class TestContratosYErroresRN15(unittest.TestCase):
    """RNF 4 y 5: DTOs de entrada con extra='forbid', sin exposición de errores de BD."""

    def test_01_todos_los_dtos_de_entrada_tienen_extra_forbid(self) -> None:
        modulos_schemas = [
            app.modules.autores.schemas,
            app.modules.clientes.schemas,
            app.modules.editoriales.schemas,
            app.modules.generos.schemas,
            app.modules.libros.schemas,
            app.modules.usuarios.schemas,
            app.modules.ventas.schemas,
        ]
        sufijos_entrada = ("Create", "Update", "Request")
        dtos_verificados = 0
        for mod in modulos_schemas:
            for nombre, cls in inspect.getmembers(mod, inspect.isclass):
                if not issubclass(cls, BaseModel) or cls is BaseModel:
                    continue
                if nombre.endswith(sufijos_entrada):
                    dtos_verificados += 1
                    extra_cfg = cls.model_config.get("extra")
                    self.assertEqual(
                        extra_cfg,
                        "forbid",
                        f"El DTO de entrada {mod.__name__}.{nombre} tiene extra={extra_cfg!r}",
                    )
        self.assertGreaterEqual(dtos_verificados, 15)

    def test_02_conflicto_por_integridad_nunca_filtra_texto_interno_de_base(self) -> None:
        from sqlalchemy.exc import IntegrityError

        for codigo in ("23505", "23503", "23514", "23001"):
            class _OrigFalso:
                sqlstate = codigo

                def __str__(self) -> str:
                    return 'DETAIL: Key (email)=(secreto@db.internal) already exists in table "usuario"'

            exc_db = IntegrityError("INSERT INTO usuario ...", {}, _OrigFalso())
            conflicto = conflicto_por_integridad(
                exc_db,
                detalle_unique="El recurso ya existe",
                detalle_fk="Referencia inexistente",
                detalle_check="Valor fuera de rango",
            )
            self.assertNotIn("DETAIL:", conflicto.mensaje)
            self.assertNotIn("secreto@db.internal", conflicto.mensaje)
            self.assertNotIn("INSERT INTO", conflicto.mensaje)

    def test_03_token_solo_se_lee_de_cookie_y_nunca_de_header_authorization(self) -> None:
        for py_file in (ROOT_DIR / "app").rglob("*.py"):
            contenido = py_file.read_text(encoding="utf-8")
            self.assertNotIn(
                "HTTPBearer",
                contenido,
                f"{py_file.name} no debe usar HTTPBearer",
            )
            self.assertNotIn(
                "OAuth2PasswordBearer",
                contenido,
                f"{py_file.name} no debe usar OAuth2PasswordBearer",
            )


class TestArchivosHttpConsistenciaRNF(unittest.TestCase):
    """RNF 6: Consistencia de archivos .http en test/ (REST Client $.id, paginación y login)."""

    def test_01_archivos_http_usan_jsonpath_con_signo_pesos_y_paginacion_nueva(self) -> None:
        carpeta_test = ROOT_DIR / "test"
        archivos_http = sorted(carpeta_test.glob("*.http"))
        self.assertGreaterEqual(len(archivos_http), 8)

        patron_sin_pesos = re.compile(r"\{\{[a-zA-Z0-9_]+\.response\.body\.(?!\$)[a-zA-Z0-9_]+\}\}")
        patron_paginacion_vieja = re.compile(r"\?(limit|offset)=")

        for archivo in archivos_http:
            contenido = archivo.read_text(encoding="utf-8")
            coincidencias_sin_pesos = patron_sin_pesos.findall(contenido)
            self.assertEqual(
                coincidencias_sin_pesos,
                [],
                f"{archivo.name} usa referencias sin '$.': {coincidencias_sin_pesos}",
            )
            coincidencias_pag_vieja = patron_paginacion_vieja.findall(contenido)
            self.assertEqual(
                coincidencias_pag_vieja,
                [],
                f"{archivo.name} usa parámetros viejos limit/offset en lugar de page/size",
            )

    def test_02_archivos_http_de_catalogo_incluyen_login_admin(self) -> None:
        for nombre in ("autores.http", "editoriales.http", "generos.http"):
            contenido = (ROOT_DIR / "test" / nombre).read_text(encoding="utf-8")
            self.assertIn(
                "/auth/login",
                contenido,
                f"{nombre} realiza POST/PATCH protegidos por ADMIN pero no inicia sesión",
            )


if __name__ == "__main__":
    unittest.main()
