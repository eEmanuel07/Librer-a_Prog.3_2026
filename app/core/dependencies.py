"""Dependencias compartidas de autenticación y autorización."""

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import TokenInvalidoError, decodificar_access_token
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.repository import AsignacionRolRepository, UsuarioRepository


async def get_usuario_actual(
    request: Request,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Usuario:
    """Extrae y valida el usuario activo a partir de la cookie access_token.

    Responde 401 si:
    - No se envía la cookie access_token.
    - El token es inválido o venció.
    - El usuario indicado en el token no existe en la base.
    - El usuario está inactivo (activo=False).
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )

    try:
        payload = decodificar_access_token(token, settings=settings)
    except TokenInvalidoError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o vencido",
        ) from exc

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        ) from exc

    usuario = await UsuarioRepository(session).get_by_id(user_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o inexistente",
        )

    # Adjuntar al request.state los roles informativos del token
    request.state.roles_token = payload.get("roles", [])
    return usuario


def get_roles_token(request: Request) -> list[str]:
    """Obtiene los roles que venían en el token JWT del usuario actual."""
    return getattr(request.state, "roles_token", [])


async def verificar_cambio_password_pendiente(
    usuario: Usuario = Depends(get_usuario_actual),
) -> Usuario:
    """Bloquea con 403 el acceso al grupo protegido si debe_cambiar_password es True (RN-06).

    Se monta una sola vez en el APIRouter del grupo protegido en main.py.
    """
    if usuario.debe_cambiar_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debe cambiar su contraseña provisoria antes de continuar",
        )
    return usuario


def requiere_rol(*roles_permitidos: str) -> Callable[..., Awaitable[Usuario]]:
    """Verifica que el usuario autenticado tenga al menos uno de los roles vigentes en la base (RN-04).

    Los roles del token son solo informativos: en cada petición se consultan las
    asignaciones no revocadas y sin vencer en la base de datos con la misma sesión
    de ``get_session``. Si no tiene el rol, responde 403; si lo tiene, devuelve el
    objeto ``Usuario``.
    """
    if not roles_permitidos:
        raise ValueError("Se debe indicar al menos un rol permitido.")
    roles_esperados = set(roles_permitidos)

    async def _verificar_rol(
        usuario: Usuario = Depends(get_usuario_actual),
        session: AsyncSession = Depends(get_session),
    ) -> Usuario:
        roles_vigentes = await AsignacionRolRepository(session).listar_roles_vigentes(
            usuario.id
        )
        if not roles_esperados.intersection(roles_vigentes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta acción",
            )
        return usuario

    return _verificar_rol
