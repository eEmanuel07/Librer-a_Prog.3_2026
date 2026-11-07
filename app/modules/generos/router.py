from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import requiere_rol
from app.core.errors import Conflicto, NoEncontrado
from app.core.paginacion import Pagina, ParametrosPagina, parametros_pagina
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead, LibroDeGenero
from app.modules.generos.unit_of_work import GeneroUnitOfWork, get_generos_uow
from app.modules.usuarios.models import Usuario

router_publico = APIRouter(prefix="/generos", tags=["generos"])
router_protegido = APIRouter(prefix="/generos", tags=["generos"])


@router_protegido.post("/", response_model=GeneroRead, status_code=status.HTTP_201_CREATED)
async def crear_genero(
    datos: GeneroCreate,
    _actor: Usuario = Depends(requiere_rol("ADMIN")),
    uow: GeneroUnitOfWork = Depends(get_generos_uow),
) -> GeneroRead:
    try:
        return await service.crear_genero(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router_publico.get("/", response_model=Pagina[GeneroRead])
async def listar_generos(
    params: ParametrosPagina = Depends(parametros_pagina),
    uow: GeneroUnitOfWork = Depends(get_generos_uow),
) -> Pagina[GeneroRead]:
    return await service.listar_generos(uow, params)


@router_publico.get("/{genero_id}/libros", response_model=Pagina[LibroDeGenero])
async def listar_libros_de_genero(
    genero_id: int,
    params: ParametrosPagina = Depends(parametros_pagina),
    uow: GeneroUnitOfWork = Depends(get_generos_uow),
) -> Pagina[LibroDeGenero]:
    try:
        return await service.listar_libros_de_genero(uow, genero_id, params)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


router = APIRouter()
router.include_router(router_publico)
router.include_router(router_protegido)
