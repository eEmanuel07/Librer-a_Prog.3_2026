from functools import lru_cache

from pydantic import Field, SecretStr, ValidationError, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Base de datos ---
    postgres_user: str = "postgres"
    postgres_password: SecretStr = Field(min_length=1)  # sin valor por defecto
    postgres_db: str = "libreria"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Pool del motor (sección 4.5): conexiones abiertas y extra en un pico.
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)

    sql_echo: bool = False

    # --- Token y cookie ---
    jwt_secret: SecretStr = Field(min_length=32)  # sin valor por defecto
    jwt_expira_minutos: int = Field(default=30, ge=1)
    cookie_secure: bool = False  # true sólo detrás de HTTPS

    # --- Contraseñas ---
    # Costo de bcrypt: se sube con los años, por eso no va fijo en el código.
    bcrypt_costo: int = Field(default=12, ge=4, le=31)
    # Cuántos bcrypt corren a la vez (el semáforo de la sección 5.6).
    bcrypt_concurrencia: int = Field(default=4, ge=1)

    @computed_field(repr=False)  # repr=False: la URL lleva la contraseña
    @property
    def database_url(self) -> str:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as error:
        variables = ", ".join(
            str(detalle["loc"][0]).upper() for detalle in error.errors() if detalle["loc"]
        )
        raise RuntimeError(
            f"Configuración incompleta o inválida: {variables}. "
            "Copiá env.example como .env y completalo (ver README)."
        ) from None
