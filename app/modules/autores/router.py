from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import requiere_rol
from app.core.errors import Conflicto, NoEncontrado
from app.core.paginacion import Pagina, ParametrosPagina, parametros_pagina
from app.modules.autores import service
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate, LibroDeAutor
from app.modules.autores.unit_of_work import AutorUnitOfWork, get_autores_uow
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/autores", tags=["autores"])


@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
async def crear_autor(
    datos: AutorCreate,
    _actor: Usuario = Depends(requiere_rol("ADMIN")),
    uow: AutorUnitOfWork = Depends(get_autores_uow),
) -> AutorRead:
    try:
        return await service.crear_autor(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{autor_id}", response_model=AutorRead)
async def obtener_autor(
    autor_id: int,
    uow: AutorUnitOfWork = Depends(get_autores_uow),
) -> AutorRead:
    try:
        return await service.obtener_autor(uow, autor_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router.patch("/{autor_id}", response_model=AutorRead)
async def actualizar_autor(
    autor_id: int,
    datos: AutorUpdate,
    _actor: Usuario = Depends(requiere_rol("ADMIN")),
    uow: AutorUnitOfWork = Depends(get_autores_uow),
) -> AutorRead:
    try:
        return await service.actualizar_autor(uow, autor_id, datos)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{autor_id}/libros", response_model=Pagina[LibroDeAutor])
async def listar_libros_de_autor(
    autor_id: int,
    params: ParametrosPagina = Depends(parametros_pagina),
    uow: AutorUnitOfWork = Depends(get_autores_uow),
) -> Pagina[LibroDeAutor]:
    try:
        return await service.listar_libros_de_autor(uow, autor_id, params)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
