from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.repository import BaseRepository
from app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)


class UsuarioRepository(BaseRepository[Usuario]):
    """Operaciones de persistencia para el modelo Usuario."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Usuario)

    async def get_by_email(self, email: str) -> Usuario | None:
        """Obtiene un usuario por su correo electrónico."""
        statement = select(Usuario).where(Usuario.email == email)
        return (await self.session.exec(statement)).first()


class AsignacionRolRepository(BaseRepository[AsignacionRol]):
    """Operaciones de consulta y persistencia para asignaciones de roles."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AsignacionRol)

    async def listar_roles_vigentes(
        self, usuario_id: int, ahora: datetime | None = None
    ) -> list[str]:
        """Obtiene los roles vigentes (no revocados y sin vencer) de un usuario."""
        instante = ahora or datetime.now(timezone.utc)
        statement = (
            select(AsignacionRol.rol)
            .where(
                AsignacionRol.usuario_id == usuario_id,
                AsignacionRol.revocada_en.is_(None),
                (AsignacionRol.vence_en.is_(None) | (AsignacionRol.vence_en > instante)),
            )
            .order_by(AsignacionRol.rol)
        )
        return list((await self.session.exec(statement)).all())

    async def obtener_abierta(self, usuario_id: int, rol: str) -> AsignacionRol | None:
        """Devuelve la asignación sin revocar (revocada_en IS NULL) de ese rol, o None."""
        statement = select(AsignacionRol).where(
            AsignacionRol.usuario_id == usuario_id,
            AsignacionRol.rol == rol,
            AsignacionRol.revocada_en.is_(None),
        )
        return (await self.session.exec(statement)).first()

    async def listar_de_usuario(self, usuario_id: int) -> Sequence[AsignacionRol]:
        """Lista todas las asignaciones de rol de un usuario (vigentes, vencidas y revocadas)."""
        statement = (
            select(AsignacionRol)
            .where(AsignacionRol.usuario_id == usuario_id)
            .order_by(AsignacionRol.id)
        )
        return (await self.session.exec(statement)).all()

    async def contar_admins_vigentes(self, ahora: datetime | None = None) -> int:
        """Cuenta cuántos usuarios activos tienen el rol ADMIN vigente (RN-05)."""
        instante = ahora or datetime.now(timezone.utc)
        statement = (
            select(func.count(func.distinct(AsignacionRol.usuario_id)))
            .join(Usuario, Usuario.id == AsignacionRol.usuario_id)
            .where(
                Usuario.activo.is_(True),
                AsignacionRol.rol == "ADMIN",
                AsignacionRol.revocada_en.is_(None),
                (AsignacionRol.vence_en.is_(None) | (AsignacionRol.vence_en > instante)),
            )
        )
        cantidad = (await self.session.exec(statement)).one()
        return int(cantidad or 0)


class IntentoAccesoRepository(BaseRepository[IntentoAcceso]):
    """Consultas sobre intentos de acceso (RN-07). Nunca confirma: eso es del UoW."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, IntentoAcceso)

    async def contar_fallos_vigentes_y_primer_fallo(
        self,
        email: str,
        ip: str,
        desde: datetime,
    ) -> tuple[int, datetime | None]:
        """Cuenta en una sola consulta los fallos vigentes de (email, ip) desde ``desde``.

        Un login correcto reinicia la cuenta (RN-07): los fallos anteriores al
        último intento con ``exito = True`` siguen en la tabla, pero dejan de
        contar gracias a la subconsulta escalar ``ultimo_exito``.
        """
        ultimo_exito = (
            select(func.max(IntentoAcceso.cuando))
            .where(
                IntentoAcceso.email == email,
                IntentoAcceso.ip == ip,
                IntentoAcceso.exito.is_(True),
            )
            .scalar_subquery()
        )
        consulta = select(
            func.count(IntentoAcceso.id),
            func.min(IntentoAcceso.cuando),
        ).where(
            IntentoAcceso.email == email,
            IntentoAcceso.ip == ip,
            IntentoAcceso.exito.is_(False),
            IntentoAcceso.cuando >= desde,
            ultimo_exito.is_(None) | (IntentoAcceso.cuando > ultimo_exito),
        )
        cantidad, primer_fallo = (await self.session.exec(consulta)).one()
        total = int(cantidad or 0)
        return total, (primer_fallo if total > 0 else None)


class EventoSeguridadRepository(BaseRepository[EventoSeguridad]):
    """Operaciones de persistencia para la bitácora de auditoría (RN-16)."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EventoSeguridad)
