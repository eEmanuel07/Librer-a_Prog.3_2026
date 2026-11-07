"""Contratos de entrada y salida para el módulo usuarios."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.security import PasswordBcrypt
from app.modules.usuarios.models import AsignacionRol

RolNombre = Literal["ADMIN", "VENDEDOR", "CLIENTE"]


class CredencialesInvalidasError(Exception):
    """Lanzada cuando el correo o contraseña son incorrectos, o el usuario está inactivo."""

    def __init__(self, mensaje: str = "Credenciales inválidas") -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class LimiteIntentosError(Exception):
    """Lanzada cuando se supera el límite de intentos fallidos de login (RN-07)."""

    def __init__(self, retry_after: int) -> None:
        super().__init__("Demasiados intentos fallidos. Intente más tarde.")
        self.retry_after = retry_after


class StrictSchema(BaseModel):
    """Contrato base que prohíbe campos no declarados (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


# --- Contratos de Login ---


class LoginRequest(StrictSchema):
    """Datos de entrada para inicio de sesión."""

    email: EmailStr
    password: PasswordBcrypt


class LoginResponse(BaseModel):
    """Respuesta al iniciar sesión exitosamente."""

    model_config = ConfigDict(from_attributes=True)

    mensaje: str = "Sesión iniciada"
    debe_cambiar_password: bool
    expira_en_segundos: int


def _normalizar_email(valor: object) -> object:
    return valor.strip().lower() if isinstance(valor, str) else valor


def _validar_nombre_no_vacio(valor: object) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("El nombre no puede estar vacío.")
    return valor.strip()


# --- Contratos de Registro ---


class RegistroRequest(StrictSchema):
    """Datos de entrada para auto-registro de clientes en la web (RN-02)."""

    nombre: str
    email: EmailStr
    password: PasswordBcrypt

    _email_normalizado = field_validator("email", mode="before")(_normalizar_email)
    _nombre_normalizado = field_validator("nombre", mode="before")(_validar_nombre_no_vacio)


class RegistroResponse(BaseModel):
    """Respuesta tras auto-registro exitoso de cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nombre: str
    cliente_id: int
    mensaje: str = "Usuario registrado exitosamente"


# --- Contratos de Sesión y Perfil ---


class MensajeResponse(BaseModel):
    """Respuesta estándar para operaciones informativas."""

    mensaje: str


class YoResponse(BaseModel):
    """Información del usuario autenticado y sus roles."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nombre: str
    debe_cambiar_password: bool
    roles: list[str]
    roles_token: list[str]


class CambioPasswordRequest(StrictSchema):
    """Datos para cambio de contraseña propio."""

    password_actual: PasswordBcrypt
    password_nueva: PasswordBcrypt


# --- Contratos de Roles con Vigencia (Ej. 5 / [R5]) ---


def _asegurar_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class AsignarRolRequest(StrictSchema):
    """Datos de entrada para asignar un rol con vigencia opcional."""

    rol: RolNombre
    vence_en: datetime | None = None

    @field_validator("vence_en")
    @classmethod
    def validar_vencimiento_con_zona_y_futuro(
        cls, valor: datetime | None
    ) -> datetime | None:
        if valor is None:
            return None
        if valor.tzinfo is None or valor.utcoffset() is None:
            raise ValueError("La fecha de vencimiento debe incluir zona horaria.")
        if valor <= datetime.now(timezone.utc):
            raise ValueError("La fecha de vencimiento debe estar en el futuro.")
        return valor


class AsignacionRolRead(BaseModel):
    """Representación de una asignación de rol (vigente, vencida o revocada)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    rol: str
    desde: datetime
    vence_en: datetime | None = None
    revocada_en: datetime | None = None
    otorgada_por: int | None = None
    vigente: bool

    @classmethod
    def desde_modelo(
        cls, asignacion: AsignacionRol, ahora: datetime | None = None
    ) -> "AsignacionRolRead":
        instante = ahora or datetime.now(timezone.utc)
        vence = _asegurar_utc(asignacion.vence_en)
        es_vigente = asignacion.revocada_en is None and (
            vence is None or vence > instante
        )
        return cls(
            id=asignacion.id,
            usuario_id=asignacion.usuario_id,
            rol=asignacion.rol,
            desde=asignacion.desde,
            vence_en=asignacion.vence_en,
            revocada_en=asignacion.revocada_en,
            otorgada_por=asignacion.otorgada_por,
            vigente=es_vigente,
        )
