"""Contratos de entrada y salida para el módulo usuarios."""

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.security import PasswordBcrypt


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

