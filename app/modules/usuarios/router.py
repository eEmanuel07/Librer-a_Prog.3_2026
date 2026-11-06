"""Rutas HTTP para el módulo usuarios (autenticación y cuentas)."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import Conflicto
from app.core.security import calcular_hash_ficticio
from app.modules.usuarios.schemas import (
    CredencialesInvalidasError,
    LimiteIntentosError,
    LoginRequest,
    LoginResponse,
    RegistroRequest,
    RegistroResponse,
)
from app.modules.usuarios.service import (
    login as service_login,
    registrar as service_registrar,
)
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork, get_usuario_uow

router = APIRouter(prefix="/auth", tags=["auth"])


def _obtener_ip_cliente(request: Request) -> str:
    """Extrae la dirección IP del cliente desde el objeto Request."""
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


@router.post("/login", response_model=LoginResponse)
async def login(
    datos: LoginRequest,
    request: Request,
    response: Response,
    uow: UsuarioUnitOfWork = Depends(get_usuario_uow),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Inicia sesión, fija la cookie HttpOnly access_token y responde con la vigencia."""
    ip = _obtener_ip_cliente(request)
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory

    hash_ficticio = getattr(request.app.state, "hash_ficticio", None)
    if hash_ficticio is None:
        hash_ficticio = await calcular_hash_ficticio(settings)

    try:
        usuario, token = await service_login(
            datos=datos,
            ip=ip,
            uow=uow,
            session_factory=session_factory,
            settings=settings,
            hash_ficticio=hash_ficticio,
        )
    except LimiteIntentosError as exc:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Intente más tarde.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    except CredencialesInvalidasError as exc:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas",
        ) from exc

    # Duración de la cookie en segundos
    max_age_segundos = settings.jwt_expira_minutos * 60

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=max_age_segundos,
        secure=settings.cookie_secure,
    )

    return LoginResponse(
        mensaje="Sesión iniciada",
        debe_cambiar_password=usuario.debe_cambiar_password,
        expira_en_segundos=max_age_segundos,
    )


@router.post("/registro", response_model=RegistroResponse, status_code=201)
async def registro(
    datos: RegistroRequest,
    uow: UsuarioUnitOfWork = Depends(get_usuario_uow),
    settings: Settings = Depends(get_settings),
) -> RegistroResponse:
    """Registra una cuenta de cliente y usuario en la web (RN-02)."""
    try:
        return await service_registrar(datos=datos, uow=uow, settings=settings)
    except Conflicto as exc:
        raise HTTPException(
            status_code=409,
            detail=exc.mensaje,
        ) from exc
