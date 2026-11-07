from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import requiere_rol
from app.core.errors import Conflicto, NoEncontrado
from app.core.paginacion import Pagina, ParametrosPagina, parametros_pagina
from app.modules.editoriales import service
from app.modules.editoriales.schemas import (
    EditorialCreate,
    EditorialRead,
    EditorialUpdate,
    LibroDeEditorial,
)
from app.modules.editoriales.unit_of_work import EditorialUnitOfWork, get_editoriales_uow
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/editoriales", tags=["editoriales"])


@router.post("/", response_model=EditorialRead, status_code=status.HTTP_201_CREATED)
async def crear_editorial(
    datos: EditorialCreate,
    _actor: Usuario = Depends(requiere_rol("ADMIN")),
    uow: EditorialUnitOfWork = Depends(get_editoriales_uow),
) -> EditorialRead:
    try:
        return await service.crear_editorial(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/", response_model=Pagina[EditorialRead])
async def listar_editoriales(
    params: ParametrosPagina = Depends(parametros_pagina),
    uow: EditorialUnitOfWork = Depends(get_editoriales_uow),
) -> Pagina[EditorialRead]:
    return await service.listar_editoriales(uow, params)


@router.get("/{editorial_id}", response_model=EditorialRead)
async def obtener_editorial(
    editorial_id: int,
    uow: EditorialUnitOfWork = Depends(get_editoriales_uow),
) -> EditorialRead:
    try:
        return await service.obtener_editorial(uow, editorial_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router.patch("/{editorial_id}", response_model=EditorialRead)
async def actualizar_editorial(
    editorial_id: int,
    datos: EditorialUpdate,
    _actor: Usuario = Depends(requiere_rol("ADMIN")),
    uow: EditorialUnitOfWork = Depends(get_editoriales_uow),
) -> EditorialRead:
    try:
        return await service.actualizar_editorial(uow, editorial_id, datos)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{editorial_id}/libros", response_model=Pagina[LibroDeEditorial])
async def listar_libros_de_editorial(
    editorial_id: int,
    params: ParametrosPagina = Depends(parametros_pagina),
    uow: EditorialUnitOfWork = Depends(get_editoriales_uow),
) -> Pagina[LibroDeEditorial]:
    try:
        return await service.listar_libros_de_editorial(uow, editorial_id, params)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
