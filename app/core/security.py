"""Seguridad: hash de contraseñas con bcrypt y firma/verificación de tokens JWT.

- Toda llamada a bcrypt corre fuera del bucle de eventos (``asyncio.to_thread``)
  y bajo un semáforo que limita cuántas corren a la vez (secciones 5.4 y 5.6).
- El costo de bcrypt y la concurrencia máxima salen de ``Settings``, nunca fijos
  en el código (sección 5.12).
- Todo campo de contraseña que termina en bcrypt acepta como máximo 72 bytes en
  UTF-8 (``PasswordBcrypt``): desde bcrypt 5.0 superar 72 bytes lanza ValueError,
  por lo que validarlo en el contrato garantiza responder 422 y nunca 500.
- Los tokens JWT llevan ``sub`` (id del usuario como texto), ``exp`` y ``roles``
  (los roles vigentes al emitirlo, informativos; RN-04).
"""

import asyncio
import secrets
import weakref
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import bcrypt
import jwt
from pydantic import AfterValidator

from app.core.config import Settings, get_settings

MAX_BYTES_BCRYPT = 72
ALGORITMO_JWT = "HS256"

# Semáforo por bucle de eventos, creado bajo demanda y nunca al importar el
# módulo (sección 1.9: al importar todavía no existe el bucle de eventos).
_SEMAFOROS_POR_LOOP: weakref.WeakKeyDictionary[
    asyncio.AbstractEventLoop, asyncio.Semaphore
] = weakref.WeakKeyDictionary()


class TokenInvalidoError(Exception):
    """El token JWT no se pudo decodificar, tiene firma inválida o venció."""


def validar_password_bcrypt(valor: str) -> str:
    """Valida que la contraseña tenga entre 1 y 72 bytes en UTF-8.

    bcrypt trunca o rechaza (desde la versión 5) todo lo que pase de 72 bytes.
    Son bytes y no caracteres: una «ñ» ocupa dos bytes en UTF-8.
    """
    if not isinstance(valor, str):
        raise ValueError("La contraseña debe ser una cadena de texto.")
    largo_bytes = len(valor.encode("utf-8"))
    if largo_bytes < 1:
        raise ValueError("La contraseña no puede estar vacía.")
    if largo_bytes > MAX_BYTES_BCRYPT:
        raise ValueError(
            f"La contraseña no puede superar los {MAX_BYTES_BCRYPT} bytes en UTF-8."
        )
    return valor


PasswordBcrypt = Annotated[str, AfterValidator(validar_password_bcrypt)]
PasswordBcryptStr = PasswordBcrypt


def obtener_semaforo_bcrypt(settings: Settings | None = None) -> asyncio.Semaphore:
    """Devuelve el semáforo de bcrypt asociado al bucle de eventos actual."""
    loop = asyncio.get_running_loop()
    semaforo = _SEMAFOROS_POR_LOOP.get(loop)
    if semaforo is None:
        cfg = settings or get_settings()
        semaforo = asyncio.Semaphore(cfg.bcrypt_concurrencia)
        _SEMAFOROS_POR_LOOP[loop] = semaforo
    return semaforo


async def hashear_password(
    password: str,
    settings: Settings | None = None,
    semaforo: asyncio.Semaphore | None = None,
) -> str:
    """Calcula el hash bcrypt fuera del bucle de eventos y bajo semáforo.

    Debe llamarse antes de abrir la transacción para no retener una conexión
    del pool durante el cálculo (sección 5.6).
    """
    validar_password_bcrypt(password)
    cfg = settings or get_settings()
    sem = semaforo or obtener_semaforo_bcrypt(cfg)
    password_bytes = password.encode("utf-8")

    async with sem:
        hash_bytes = await asyncio.to_thread(
            bcrypt.hashpw,
            password_bytes,
            bcrypt.gensalt(rounds=cfg.bcrypt_costo),
        )
    return hash_bytes.decode("utf-8")


async def verificar_password(
    password: str,
    password_hash: str | bytes,
    semaforo: asyncio.Semaphore | None = None,
    settings: Settings | None = None,
) -> bool:
    """Verifica una contraseña contra su hash bcrypt fuera del bucle y bajo semáforo."""
    validar_password_bcrypt(password)
    sem = semaforo or obtener_semaforo_bcrypt(settings)
    password_bytes = password.encode("utf-8")
    hash_bytes = (
        password_hash.encode("utf-8")
        if isinstance(password_hash, str)
        else password_hash
    )

    async with sem:
        return await asyncio.to_thread(
            bcrypt.checkpw,
            password_bytes,
            hash_bytes,
        )


async def calcular_hash_ficticio(
    settings: Settings | None = None,
    semaforo: asyncio.Semaphore | None = None,
) -> str:
    """Calcula una vez en el lifespan el hash ficticio para el login (RN-08).

    Usa una clave aleatoria descartable con el mismo costo de Settings para que
    verificar un correo inexistente tarde lo mismo que uno existente.
    """
    clave_descartable = secrets.token_urlsafe(24)
    return await hashear_password(
        clave_descartable,
        settings=settings,
        semaforo=semaforo,
    )


def crear_access_token(
    usuario_id: int,
    roles: Sequence[str],
    settings: Settings | None = None,
    ahora: datetime | None = None,
) -> str:
    """Emite un JWT firmado con ``sub``, ``exp`` y los roles vigentes al emitirlo."""
    cfg = settings or get_settings()
    instante = ahora or datetime.now(timezone.utc)
    expiracion = instante + timedelta(minutes=cfg.jwt_expira_minutos)

    payload: dict[str, Any] = {
        "sub": str(usuario_id),
        "exp": int(expiracion.timestamp()),
        "roles": list(roles),
    }
    return jwt.encode(
        payload,
        cfg.jwt_secret.get_secret_value(),
        algorithm=ALGORITMO_JWT,
    )


def decodificar_access_token(
    token: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Verifica firma y vigencia de un JWT y devuelve su payload.

    Lanza ``TokenInvalidoError`` si el token es inválido, venció o le faltan
    los claims obligatorios (``sub``, ``exp``).
    """
    cfg = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            cfg.jwt_secret.get_secret_value(),
            algorithms=[ALGORITMO_JWT],
            options={"require": ["sub", "exp"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenInvalidoError("El token ha vencido.") from exc
    except jwt.PyJWTError as exc:
        raise TokenInvalidoError("El token es inválido.") from exc

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise TokenInvalidoError("El claim sub del token es inválido.")
    return payload


crear_token_acceso = crear_access_token
decodificar_token_acceso = decodificar_access_token
