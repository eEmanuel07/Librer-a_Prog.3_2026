"""Reglas de negocio del módulo usuarios."""

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings
from app.core.security import crear_access_token, verificar_password
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import (
    CredencialesInvalidasError,
    LimiteIntentosError,
    LoginRequest,
)
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork, registrar_intento_acceso

MAX_FALLOS = 5
VENTANA_SEGUNDOS = 60


async def login(
    datos: LoginRequest,
    ip: str,
    uow: UsuarioUnitOfWork,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    hash_ficticio: str,
) -> tuple[Usuario, str]:
    """Inicia sesión con protección de límite de intentos y prevención de enumeración (RN-07, RN-08).

    Orden estricto:
    1. Límite de 5 intentos fallidos en 60s por (email, ip): responde 429 con Retry-After sin calcular hash.
    2. Verificación de contraseña fuera de la transacción (contra hash del usuario o hash ficticio).
    3. Registro del intento en sesión y transacción propias (confirmadas siempre).
    4. Si falla la verificación, lanza CredencialesInvalidasError (401).
    5. Si tiene éxito, emite JWT con roles vigentes al momento del login.
    """
    ahora = datetime.now(timezone.utc)
    desde = ahora - timedelta(seconds=VENTANA_SEGUNDOS)

    # 1. Límite de intentos (RN-07): una consulta, sin hash
    async with uow:
        cantidad, primer_fallo = await uow.intentos_acceso.contar_fallos_vigentes_y_primer_fallo(
            datos.email, ip, desde
        )
        if cantidad >= MAX_FALLOS:
            pf = primer_fallo or desde
            if pf.tzinfo is None:
                pf = pf.replace(tzinfo=timezone.utc)
            restante = pf + timedelta(seconds=VENTANA_SEGUNDOS) - ahora
            segundos = max(1, math.ceil(restante.total_seconds()))
            raise LimiteIntentosError(retry_after=segundos)

        usuario = await uow.usuarios.get_by_email(datos.email)

    # 2. Verificación de contraseña con bcrypt (RN-08): fuera de la transacción para no tomar conexión
    if usuario is not None and usuario.activo:
        es_valido = await verificar_password(datos.password, usuario.password_hash, settings=settings)
    else:
        await verificar_password(datos.password, hash_ficticio, settings=settings)
        es_valido = False

    # 3. Anotar intento en sesión propia (Ejercicio 7, sección 6.8.1)
    await registrar_intento_acceso(
        session_factory,
        email=datos.email,
        ip=ip,
        exito=es_valido,
        cuando=ahora,
    )

    if not es_valido or usuario is None:
        raise CredencialesInvalidasError("Credenciales inválidas")

    # 4. Obtener roles vigentes y emitir token firmado
    async with uow:
        roles = await uow.asignaciones_rol.listar_roles_vigentes(usuario.id)

    token = crear_access_token(usuario.id, roles, settings=settings)
    return usuario, token
