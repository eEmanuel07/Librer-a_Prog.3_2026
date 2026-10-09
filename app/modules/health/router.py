from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.health import service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    # No toca la base.
    return service.estado_vivo()


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        return await service.estado_base(session)
    except (SQLAlchemyError, OSError):
        # RN-12: mensaje propio, nunca el texto de la base.
        raise HTTPException(status_code=503, detail="La base de datos no está disponible")
