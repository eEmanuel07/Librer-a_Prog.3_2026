"""Rutas HTTP para el módulo usuarios (autenticación, cuentas y roles)."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import get_usuario_actual, requiere_rol
from app.core.errors import Conflicto, NoEncontrado
from app.core.security import calcular_hash_ficticio
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import (
    AsignacionRolRead,
    AsignarRolRequest,
    CambioPasswordRequest,
    CrearPersonalRequest,
    CredencialesInvalidasError,
    LimiteIntentosError,
    LoginRequest,
    LoginResponse,
    MensajeResponse,
    RegistroRequest,
    RegistroResponse,
    RolNombre,
    UsuarioRead,
    YoResponse,
)
from app.modules.usuarios.service import (
    asignar_rol as service_asignar_rol,
    cambiar_password as service_cambiar_password,
    crear_personal as service_crear_personal,
    listar_roles_usuario as service_listar_roles_usuario,
    login as service_login,
    obtener_yo as service_obtener_yo,
    registrar as service_registrar,
    revocar_rol as service_revocar_rol,
)
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork, get_usuario_uow

router = APIRouter(prefix="/auth", tags=["auth"])
router_usuarios = APIRouter(prefix="/usuarios", tags=["usuarios"])


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


@router.post("/logout", response_model=MensajeResponse)
async def logout(response: Response) -> MensajeResponse:
    """Cierra la sesión eliminando la cookie HttpOnly access_token."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
    )
    return MensajeResponse(mensaje="Sesión cerrada")


@router.get("/yo", response_model=YoResponse)
async def yo(
    request: Request,
    usuario: Usuario = Depends(get_usuario_actual),
    uow: UsuarioUnitOfWork = Depends(get_usuario_uow),
) -> YoResponse:
    """Retorna la identidad del usuario, roles vigentes en BD y roles del token."""
    roles_token = getattr(request.state, "roles_token", [])
    return await service_obtener_yo(usuario=usuario, roles_token=roles_token, uow=uow)


@router.post("/cambiar-password", response_model=MensajeResponse)
async def cambiar_password_endpoint(
    datos: CambioPasswordRequest,
    usuario: Usuario = Depends(get_usuario_actual),
    uow: UsuarioUnitOfWork = Depends(get_usuario_uow),
    settings: Settings = Depends(get_settings),
) -> MensajeResponse:
    """Actualiza la contraseña del usuario autenticado y registra auditoría (RN-16)."""
    try:
        return await service_cambiar_password(
            datos=datos,
            usuario=usuario,
            uow=uow,
            settings=settings,
        )
    except CredencialesInvalidasError as exc:
        raise HTTPException(
            status_code=401,
            detail=exc.mensaje,
        ) from exc


# --- Rutas de Alta de Personal y Roles con Vigencia (Ej. 5 / [R4], [R5]) ---


@router_usuarios.post(
    "",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_personal_endpoint(
    datos: CrearPersonalRequest,
    actor: Usuario = Depends(requiere_rol("ADMIN")),
    uow: UsuarioUnitOfWork = Depends(get_usuario_uow),
    settings: Settings = Depends(get_settings),
) -> UsuarioRead:
    """Crea una cuenta de personal con contraseña provisoria (solo ADMIN, RN-16)."""
    try:
        return await service_crear_personal(
            uow=uow,
            datos=datos,
            actor=actor,
            settings=settings,
        )
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router_usuarios.post(
    "/{usuario_id}/roles",
    response_model=AsignacionRolRead,
    status_code=status.HTTP_201_CREATED,
)
async def asignar_rol_endpoint(
    usuario_id: int,
    datos: AsignarRolRequest,
    actor: Usuario = Depends(requiere_rol("ADMIN")),
    uow: UsuarioUnitOfWork = Depends(get_usuario_uow),
) -> AsignacionRolRead:
    """Asigna un rol con vigencia opcional al usuario indicado (solo ADMIN)."""
    try:
        return await service_asignar_rol(
            uow=uow,
            usuario_id=usuario_id,
            datos=datos,
            actor=actor,
        )
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router_usuarios.get(
    "/{usuario_id}/roles",
    response_model=list[AsignacionRolRead],
)
async def listar_roles_endpoint(
    usuario_id: int,
    _actor: Usuario = Depends(requiere_rol("ADMIN")),
    uow: UsuarioUnitOfWork = Depends(get_usuario_uow),
) -> list[AsignacionRolRead]:
    """Lista las asignaciones de rol de un usuario (solo ADMIN)."""
    try:
        return await service_listar_roles_usuario(uow=uow, usuario_id=usuario_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router_usuarios.delete(
    "/{usuario_id}/roles/{rol}",
    response_model=AsignacionRolRead,
)
async def revocar_rol_endpoint(
    usuario_id: int,
    rol: RolNombre,
    actor: Usuario = Depends(requiere_rol("ADMIN")),
    uow: UsuarioUnitOfWork = Depends(get_usuario_uow),
) -> AsignacionRolRead:
    """Revoca el rol vigente escribiendo revocada_en sin borrar la fila (solo ADMIN)."""
    try:
        return await service_revocar_rol(
            uow=uow,
            usuario_id=usuario_id,
            rol=rol,
            actor=actor,
        )
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None
