from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.usuarios.models import IntentoAcceso
from app.modules.usuarios.repository import IntentoAccesoRepository


async def registrar_intento_acceso(
    session_factory: async_sessionmaker[AsyncSession],
    email: str,
    ip: str,
    exito: bool,
    cuando: datetime | None = None,
) -> IntentoAcceso:
    """Anexa un intento de login (correcto o fallido) en ``intento_acceso``."""
    # Ejercicio 7 (sección 6.8.1) — única escritura con sesión y transacción propias:
    # 1. Qué hace distinto: abre su propia sesión desde ``session_factory`` y
    #    confirma siempre su propia transacción con ``commit()``, sin usar la
    #    sesión ni el Unit of Work de la petición.
    # 2. Por qué no puede compartir la transacción: el fallo de login (401) que
    #    se necesita contar para el límite de RN-07 es el mismo que revierte la
    #    transacción de la petición; si compartiera esa transacción, el rollback
    #    desharía el intento fallido y la cuenta nunca subiría.
    # 3. Cuál es su costo: toma una conexión adicional del pool durante esta
    #    escritura y deja filas confirmadas en ``intento_acceso`` aunque la
    #    petición falle o se revierta.
    instante = cuando if cuando is not None else datetime.now(timezone.utc)
    intento = IntentoAcceso(
        email=email,
        ip=ip,
        exito=exito,
        cuando=instante,
    )
    async with session_factory() as sesion_propia:
        await IntentoAccesoRepository(sesion_propia).add(intento)
        await sesion_propia.commit()
    return intento
