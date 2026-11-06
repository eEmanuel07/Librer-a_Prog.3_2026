"""Contratos de entrada y salida para el módulo usuarios."""

from pydantic import BaseModel, ConfigDict, EmailStr

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
