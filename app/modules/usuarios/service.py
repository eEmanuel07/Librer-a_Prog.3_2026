"""Reglas de negocio del módulo usuarios."""

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings
from app.core.errors import Conflicto, NoEncontrado
from app.core.security import crear_access_token, hashear_password, verificar_password
from app.modules.clientes.models import Cliente
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from app.modules.usuarios.schemas import (
    AsignacionRolRead,
    AsignarRolRequest,
    CambioPasswordRequest,
    CrearPersonalRequest,
    CredencialesInvalidasError,
    LimiteIntentosError,
    LoginRequest,
    MensajeResponse,
    RegistroRequest,
    RegistroResponse,
    UsuarioRead,
    YoResponse,
)
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork, registrar_intento_acceso

MAX_FALLOS = 5
VENTANA_SEGUNDOS = 60

_DETALLE_USUARIO_NO_EXISTE = "El usuario no existe"
_DETALLE_ROL_YA_VIGENTE = "El usuario ya tiene una asignación vigente de ese rol"


def _normalizar_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


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


async def registrar(
    datos: RegistroRequest,
    uow: UsuarioUnitOfWork,
    settings: Settings,
) -> RegistroResponse:
    """Registra un nuevo usuario y su ficha de cliente vinculada (RN-02).

    1. Calcula el hash bcrypt antes de abrir la transacción (fuera del pool).
    2. En un solo bloque del UoW crea:
       - Usuario (activo=True, debe_cambiar_password=False)
       - AsignacionRol (rol="CLIENTE", desde=ahora)
       - Cliente (nombre=datos.nombre, email=datos.email, usuario_id=usuario.id)
    3. Si el email ya existe (en usuario o cliente), la base rechaza con IntegrityError
       y el UoW revierte la transacción levantando Conflicto (409) con mensaje propio.
    """
    password_hash = await hashear_password(datos.password, settings=settings)
    ahora = datetime.now(timezone.utc)

    async with uow.con_mensajes(unique="El correo electrónico ya está registrado"):
        usuario = Usuario(
            nombre=datos.nombre,
            email=datos.email,
            password_hash=password_hash,
            activo=True,
            debe_cambiar_password=False,
        )
        await uow.usuarios.add(usuario)

        asignacion = AsignacionRol(
            usuario_id=usuario.id,
            rol="CLIENTE",
            desde=ahora,
        )
        await uow.asignaciones_rol.add(asignacion)

        cliente = Cliente(
            nombre=datos.nombre,
            email=datos.email,
            usuario_id=usuario.id,
        )
        uow.clientes.agregar(cliente)
        await uow.session.flush()

    return RegistroResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        cliente_id=cliente.id,
        mensaje="Usuario registrado exitosamente",
    )


async def obtener_yo(
    usuario: Usuario,
    roles_token: list[str],
    uow: UsuarioUnitOfWork,
) -> YoResponse:
    """Retorna la información del usuario autenticado, roles vigentes en BD y roles del token."""
    async with uow:
        roles_bd = await uow.asignaciones_rol.listar_roles_vigentes(usuario.id)

    return YoResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        debe_cambiar_password=usuario.debe_cambiar_password,
        roles=roles_bd,
        roles_token=roles_token,
    )


async def cambiar_password(
    datos: CambioPasswordRequest,
    usuario: Usuario,
    uow: UsuarioUnitOfWork,
    settings: Settings,
) -> MensajeResponse:
    """Actualiza la contraseña del usuario autenticado y registra auditoría (RN-16).

    1. Verifica la contraseña actual con bcrypt (fuera de la transacción).
    2. Si es incorrecta, lanza CredencialesInvalidasError.
    3. Calcula el nuevo hash bcrypt antes de abrir la transacción (fuera del pool).
    4. En un solo bloque del Unit of Work (RN-16):
       - Actualiza password_hash = nuevo_hash
       - Fija debe_cambiar_password = False
       - Anota un EventoSeguridad(actor=usuario.email, accion="Cambio de contraseña")
    """
    es_valida = await verificar_password(
        datos.password_actual,
        usuario.password_hash,
        settings=settings,
    )
    if not es_valida:
        raise CredencialesInvalidasError("Contraseña actual incorrecta")

    nuevo_hash = await hashear_password(datos.password_nueva, settings=settings)
    ahora = datetime.now(timezone.utc)

    async with uow:
        target = await uow.usuarios.get_by_id(usuario.id)
        if target is not None:
            target.password_hash = nuevo_hash
            target.debe_cambiar_password = False
            uow.usuarios.session.add(target)
        await uow.eventos.add(
            EventoSeguridad(
                actor=usuario.email,
                accion="Cambio de contraseña",
                cuando=ahora,
            )
        )

    return MensajeResponse(mensaje="Contraseña actualizada exitosamente")


# --- Roles con Vigencia (Ej. 5 / [R5]) ---


async def asignar_rol(
    uow: UsuarioUnitOfWork,
    usuario_id: int,
    datos: AsignarRolRequest,
    actor: Usuario,
) -> AsignacionRolRead:
    """Asigna un rol con vigencia opcional y registra el evento en el mismo bloque (RN-03, RN-16).

    Si el usuario tenía una asignación abierta pero ya vencida de ese rol, la
    cierra escribiendo ``revocada_en`` y abre una nueva fila. Si tenía una
    asignación vigente, responde 409.
    """
    ahora = datetime.now(timezone.utc)

    async with uow.con_mensajes(
        unique=_DETALLE_ROL_YA_VIGENTE,
        check="El rol indicado no es válido",
    ):
        usuario_destino = await uow.usuarios.get_by_id(usuario_id)
        if usuario_destino is None:
            raise NoEncontrado(_DETALLE_USUARIO_NO_EXISTE)

        abierta = await uow.asignaciones_rol.obtener_abierta(usuario_id, datos.rol)
        if abierta is not None:
            vence_anterior = _normalizar_utc(abierta.vence_en)
            if vence_anterior is not None and vence_anterior <= ahora:
                # Reasignar un rol vencido cierra la fila anterior y abre una nueva.
                await uow.asignaciones_rol.update(abierta, {"revocada_en": ahora})
            else:
                raise Conflicto(_DETALLE_ROL_YA_VIGENTE)

        nueva = AsignacionRol(
            usuario_id=usuario_id,
            rol=datos.rol,
            desde=ahora,
            vence_en=datos.vence_en,
            otorgada_por=actor.id,
        )
        await uow.asignaciones_rol.add(nueva)

        await uow.eventos.add(
            EventoSeguridad(
                cuando=ahora,
                actor=actor.email,
                accion=f"Asignación de rol {datos.rol} a {usuario_destino.email}",
            )
        )

    return AsignacionRolRead.desde_modelo(nueva, ahora=ahora)


async def listar_roles_usuario(
    uow: UsuarioUnitOfWork,
    usuario_id: int,
) -> list[AsignacionRolRead]:
    """Devuelve todas las asignaciones de rol de un usuario (vigentes, vencidas y revocadas)."""
    ahora = datetime.now(timezone.utc)
    async with uow:
        usuario_destino = await uow.usuarios.get_by_id(usuario_id)
        if usuario_destino is None:
            raise NoEncontrado(_DETALLE_USUARIO_NO_EXISTE)
        asignaciones = await uow.asignaciones_rol.listar_de_usuario(usuario_id)
        return [AsignacionRolRead.desde_modelo(a, ahora=ahora) for a in asignaciones]


async def revocar_rol(
    uow: UsuarioUnitOfWork,
    usuario_id: int,
    rol: str,
    actor: Usuario,
) -> AsignacionRolRead:
    """Revoca el rol vigente escribiendo ``revocada_en`` sin borrar la fila (RN-05, RN-16)."""
    ahora = datetime.now(timezone.utc)

    async with uow:
        usuario_destino = await uow.usuarios.get_by_id(usuario_id)
        if usuario_destino is None:
            raise NoEncontrado(_DETALLE_USUARIO_NO_EXISTE)

        abierta = await uow.asignaciones_rol.obtener_abierta(usuario_id, rol)
        vence_actual = _normalizar_utc(abierta.vence_en) if abierta is not None else None
        if abierta is None or (vence_actual is not None and vence_actual <= ahora):
            raise NoEncontrado("El usuario no tiene ese rol vigente")

        if rol == "ADMIN":
            if actor.id == usuario_id:
                raise Conflicto("Un administrador no puede revocarse su propio rol ADMIN")
            admins_vigentes = await uow.asignaciones_rol.contar_admins_vigentes(ahora)
            if admins_vigentes <= 1:
                raise Conflicto("El sistema no puede quedar sin administradores vigentes")

        await uow.asignaciones_rol.update(abierta, {"revocada_en": ahora})

        await uow.eventos.add(
            EventoSeguridad(
                cuando=ahora,
                actor=actor.email,
                accion=f"Revocación de rol {rol} a {usuario_destino.email}",
            )
        )

    return AsignacionRolRead.desde_modelo(abierta, ahora=ahora)


# --- Alta de Personal (Ej. 5 / [R4]) ---


async def crear_personal(
    uow: UsuarioUnitOfWork,
    datos: CrearPersonalRequest,
    actor: Usuario,
    settings: Settings,
) -> UsuarioRead:
    """Crea una cuenta de personal con contraseña provisoria y anota el evento (RN-16).

    1. Calcula el hash bcrypt antes de abrir la transacción (fuera del pool).
    2. En un solo bloque del UoW crea el Usuario con debe_cambiar_password=True
       y la línea correspondiente en evento_seguridad.
    """
    password_hash = await hashear_password(datos.password, settings=settings)
    ahora = datetime.now(timezone.utc)

    async with uow.con_mensajes(unique="El correo electrónico ya está registrado"):
        usuario = Usuario(
            nombre=datos.nombre,
            email=datos.email,
            password_hash=password_hash,
            activo=True,
            debe_cambiar_password=True,
        )
        await uow.usuarios.add(usuario)

        await uow.eventos.add(
            EventoSeguridad(
                cuando=ahora,
                actor=actor.email,
                accion=f"Alta de personal {usuario.email}",
            )
        )

    return UsuarioRead.model_validate(usuario)
