from app.core.errors import NoEncontrado
from app.core.paginacion import Pagina, ParametrosPagina
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    LibroCreate,
    LibroRead,
    LibroResumen,
    LibroUpdate,
)
from app.modules.libros.unit_of_work import LibroUnitOfWork

# RN-15: mensajes propios para el 409; nunca el texto de la base.
_DETALLE_UNIQUE = "El ISBN ya existe en un libro vigente o un autor figura dos veces en el libro"
_DETALLE_FK = "La editorial, el género o algún autor indicado no existe"
_DETALLE_CHECK = "Los datos del libro no cumplen las reglas del catálogo"
_DETALLE_NO_EXISTE = "El libro no existe"

_MOTIVO_STOCK_INICIAL = "Stock inicial"

_MENSAJES_409 = {
    "unique": _DETALLE_UNIQUE,  # RN-01 / C-13
    "fk": _DETALLE_FK,
    "check": _DETALLE_CHECK,
}


# ---------- Lecturas con precarga (sin N+1) ----------


async def obtener_libro(uow: LibroUnitOfWork, libro_id: int) -> LibroRead:
    async with uow:
        libro = await uow.libros.obtener_con_relaciones(libro_id)
        if libro is None:
            raise NoEncontrado(_DETALLE_NO_EXISTE)
        return LibroRead.desde_modelo(libro)


async def listar_libros(
    uow: LibroUnitOfWork,
    params: ParametrosPagina,
    titulo: str | None,
    genero_id: int | None = None,
) -> Pagina[LibroResumen]:
    async with uow:
        libros, total = await uow.libros.listar_pagina(params, titulo, genero_id)
        return Pagina.armar([LibroResumen.desde_modelo(libro) for libro in libros], total, params)


# ---------- Escrituras ----------


async def crear_libro(uow: LibroUnitOfWork, datos: LibroCreate, usuario_id: int) -> LibroRead:
    """Alta del libro, sus autorías y el movimiento «Stock inicial», en un solo bloque.

    RN-11: el libro nace con stock 0 y el stock inicial entra por mover_stock, el
    único punto de escritura del stock, para que stock sea siempre la suma de los
    movimientos. Si la base rechaza algo, el UoW revierte las tres cosas juntas.

    Agregación: viajan los ids de la editorial, del género (opcional) y de cada
    autor. No se consulta antes si existen: se escribe y, si la base rechaza la
    clave foránea, se responde 409.
    """
    libro = Libro(
        isbn=datos.isbn,
        titulo=datos.titulo,
        precio=datos.precio,
        stock=0,
        editorial_id=datos.editorial_id,
        genero_id=datos.genero_id,
    )
    for autoria in datos.autores:
        libro.autorias.append(
            LibroAutor(autor_id=autoria.autor_id, rol=autoria.rol, orden=autoria.orden)
        )

    async with uow.con_mensajes(**_MENSAJES_409):
        await uow.libros.add(libro)  # flush: el libro ya tiene id para el movimiento
        if datos.stock_inicial > 0:
            # Con 0 no hay movimiento: la tabla no admite cantidad 0, y stock 0
            # ya es la suma (vacía) de los movimientos.
            await uow.libros.mover_stock(
                libro, datos.stock_inicial, _MOTIVO_STOCK_INICIAL, usuario_id
            )
    # la lectura va después de cerrar el bloque de escritura (no se anidan)
    return await obtener_libro(uow, libro.id)


async def actualizar_libro(uow: LibroUnitOfWork, libro_id: int, datos: LibroUpdate) -> LibroRead:
    async with uow.con_mensajes(**_MENSAJES_409):
        libro = await uow.libros.obtener(libro_id)
        if libro is None:
            raise NoEncontrado(_DETALLE_NO_EXISTE)
        # PATCH: sólo los campos enviados (título y precio); stock y autores no se tocan.
        await uow.libros.update(libro, datos.model_dump(exclude_unset=True))

    # la lectura va después de cerrar el bloque de escritura (no se anidan)
    return await obtener_libro(uow, libro_id)


async def dar_de_baja_libro(uow: LibroUnitOfWork, libro_id: int) -> None:
    """Baja lógica (RN-13): escribe borrado_en; la fila queda para las ventas viejas.

    Un libro ya dado de baja da 404, igual que uno que nunca existió: para el
    catálogo no está. Su ISBN queda libre para otro alta (índice único parcial).
    """
    async with uow:
        libro = await uow.libros.obtener(libro_id)
        if libro is None:
            raise NoEncontrado(_DETALLE_NO_EXISTE)
        await uow.libros.soft_delete(libro)
