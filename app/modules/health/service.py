from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession


def estado_vivo() -> dict[str, str]:
    return {"estado": "vivo"}


async def estado_base(session: AsyncSession) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"estado": "listo", "base": "ok"}
