from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    # No toca la base.
    return {"estado": "vivo"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
        return {"estado": "listo", "base": "ok"}
    except (SQLAlchemyError, OSError):
        # RN-15: mensaje propio, nunca el texto de la base.
        raise HTTPException(
            status_code=503,
            detail="La base de datos no está disponible",
        ) from None
