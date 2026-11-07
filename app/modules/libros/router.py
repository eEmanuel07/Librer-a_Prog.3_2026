from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_usuario_actual
from app.core.errors import Conflicto, NoEncontrado
from app.core.paginacion import Pagina, ParametrosPagina, parametros_pagina
from app.modules.libros import service
from app.modules.libros.schemas import (
    LibroCreate,
    LibroRead,
    LibroResumen,
    LibroUpdate,
    MovimientoRead,
    ReposicionCreate,
    ReposicionRead,
)
from app.modules.libros.unit_of_work import LibroUnitOfWork, get_libros_uow
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/libros", tags=["libros"])

# Las escrituras son del grupo protegido, rol ADMIN. Por ahora piden sesión
# (get_usuario_actual, 401); cuando entre requiere_rol (R2, #46) cada una cambia
# esa dependencia por la del rol ADMIN (403), sin tocar el service.


@router.post("/", response_model=LibroRead, status_code=status.HTTP_201_CREATED)
async def crear_libro(
    datos: LibroCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    uow: LibroUnitOfWork = Depends(get_libros_uow),
) -> LibroRead:
    try:
        return await service.crear_libro(uow, datos, usuario_id=usuario.id)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/", response_model=Pagina[LibroResumen])
async def listar_libros(
    titulo: str | None = Query(default=None, description="Parte del título, sin distinguir mayúsculas"),
    genero_id: int | None = Query(default=None, description="Sólo los libros de este género"),
    params: ParametrosPagina = Depends(parametros_pagina),
    uow: LibroUnitOfWork = Depends(get_libros_uow),
) -> Pagina[LibroResumen]:
    # Una página más allá de la última (PaginaInexistente) la responde main.py con 422.
    return await service.listar_libros(uow, params, titulo=titulo, genero_id=genero_id)


@router.get("/{libro_id}", response_model=LibroRead)
async def obtener_libro(
    libro_id: int,
    uow: LibroUnitOfWork = Depends(get_libros_uow),
) -> LibroRead:
    try:
        return await service.obtener_libro(uow, libro_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router.patch("/{libro_id}", response_model=LibroRead)
async def actualizar_libro(
    libro_id: int,
    datos: LibroUpdate,
    usuario: Usuario = Depends(get_usuario_actual),
    uow: LibroUnitOfWork = Depends(get_libros_uow),
) -> LibroRead:
    try:
        return await service.actualizar_libro(uow, libro_id, datos)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.post("/{libro_id}/reponer", response_model=ReposicionRead)
async def reponer_libro(
    libro_id: int,
    datos: ReposicionCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    uow: LibroUnitOfWork = Depends(get_libros_uow),
) -> ReposicionRead:
    try:
        return await service.reponer_libro(uow, libro_id, datos, usuario_id=usuario.id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        # RN-13: un libro dado de baja no se repone.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{libro_id}/movimientos", response_model=Pagina[MovimientoRead])
async def listar_movimientos(
    libro_id: int,
    params: ParametrosPagina = Depends(parametros_pagina),
    usuario: Usuario = Depends(get_usuario_actual),
    uow: LibroUnitOfWork = Depends(get_libros_uow),
) -> Pagina[MovimientoRead]:
    try:
        return await service.listar_movimientos(uow, libro_id, params)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router.delete("/{libro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def dar_de_baja_libro(
    libro_id: int,
    usuario: Usuario = Depends(get_usuario_actual),
    uow: LibroUnitOfWork = Depends(get_libros_uow),
) -> Response:
    try:
        await service.dar_de_baja_libro(uow, libro_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
