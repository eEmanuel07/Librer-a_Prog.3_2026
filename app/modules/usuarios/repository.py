from datetime import datetime

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.repository import BaseRepository
from app.modules.usuarios.models import IntentoAcceso


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
