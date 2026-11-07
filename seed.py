"""Datos iniciales de la librería (Parcial Cap. 1 a 6).

Se corre desde la raíz del repo:

    python seed.py

Borra todos los datos del proyecto con un único
TRUNCATE ... RESTART IDENTITY CASCADE (los ids vuelven a empezar en 1),
vuelve a insertar los datos de la consigna (págs. 19-20) y termina listando
cuántas filas quedaron en cada tabla. Como el TRUNCATE reinicia las secuencias,
correrlo varias veces produce exactamente el mismo resultado.

La URL de la base sale de Settings (.env) vía get_settings(): en el código
nunca hay contraseñas reales de la base ni claves de firma. Las contraseñas de
prueba de los 5 usuarios iniciales viven sólo en este archivo.
"""

import asyncio
import re
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlmodel import SQLModel

from app.core.config import Settings, get_settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.core.security import hashear_password
from app.modules.autores.models import Autor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor, MovimientoStock
from app.modules.libros.repository import LibroRepository
from app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)
from app.modules.ventas.models import RenglonVenta, Venta

# Importar todos los modelos garantiza que SQLModel.metadata.sorted_tables los incluya
_MODELOS = (
    Editorial,
    Genero,
    Autor,
    Libro,
    LibroAutor,
    MovimientoStock,
    Cliente,
    PerfilCliente,
    Venta,
    RenglonVenta,
    Usuario,
    AsignacionRol,
    IntentoAcceso,
    EventoSeguridad,
)

# Contraseñas de prueba para los archivos .http (viven sólo en seed.py)
CONTRASENAS_PRUEBA: dict[str, str] = {
    "admin@example.com": "Admin123!",
    "admin2@example.com": "Admin123!",
    "vendedor@example.com": "Vendedor123!",
    "ana@example.com": "Cliente123!",
    "nuevo@example.com": "Provisoria123!",
}


def url_sin_password(url: str) -> str:
    """Enmascara la contraseña para poder imprimir la URL en consola."""
    return re.sub(r":[^:@/]+@", ":***@", url)


async def _vaciar_tablas(conexion: Any) -> None:
    if conexion.dialect.name == "sqlite":
        for tabla in reversed(SQLModel.metadata.sorted_tables):
            await conexion.execute(text(f"DELETE FROM {tabla.name}"))
        return

    tablas = ", ".join(tabla.name for tabla in SQLModel.metadata.sorted_tables)
    await conexion.execute(text(f"TRUNCATE TABLE {tablas} RESTART IDENTITY CASCADE"))


async def sembrar(
    fabrica: Callable[[], Any] | None = None,
    settings: Settings | None = None,
) -> None:
    ajustes = settings or get_settings()

    print(f"Base de destino: {url_sin_password(ajustes.database_url)}")
    print("ATENCIÓN: este script borra TODOS los datos de las tablas del proyecto.")

    # Los hashes bcrypt se calculan fuera de la transacción (sección 5.6).
    hashes = {
        email: await hashear_password(clave, settings=ajustes)
        for email, clave in CONTRASENAS_PRUEBA.items()
    }

    motor = None
    if fabrica is None:
        motor = crear_motor(ajustes.database_url, echo=ajustes.sql_echo)
        fabrica = crear_fabrica_sesiones(motor)

    try:
        async with fabrica() as session:
            conexion = await session.connection()
            await _vaciar_tablas(conexion)

            # 1. Usuarios iniciales (págs. 19-20)
            admin = Usuario(
                email="admin@example.com",
                nombre="Administrador Principal",
                password_hash=hashes["admin@example.com"],
                activo=True,
                debe_cambiar_password=False,
            )
            admin2 = Usuario(
                email="admin2@example.com",
                nombre="Administrador Secundario",
                password_hash=hashes["admin2@example.com"],
                activo=True,
                debe_cambiar_password=False,
            )
            vendedor = Usuario(
                email="vendedor@example.com",
                nombre="Vendedor Mostrador",
                password_hash=hashes["vendedor@example.com"],
                activo=True,
                debe_cambiar_password=False,
            )
            usuario_ana = Usuario(
                email="ana@example.com",
                nombre="Ana Paz",
                password_hash=hashes["ana@example.com"],
                activo=True,
                debe_cambiar_password=False,
            )
            nuevo = Usuario(
                email="nuevo@example.com",
                nombre="Vendedor Nuevo",
                password_hash=hashes["nuevo@example.com"],
                activo=True,
                debe_cambiar_password=True,
            )
            session.add_all([admin, admin2, vendedor, usuario_ana, nuevo])
            await session.flush()

            session.add_all(
                [
                    AsignacionRol(usuario_id=admin.id, rol="ADMIN"),
                    AsignacionRol(usuario_id=admin2.id, rol="ADMIN"),
                    AsignacionRol(
                        usuario_id=vendedor.id,
                        rol="VENDEDOR",
                        otorgada_por=admin.id,
                    ),
                    AsignacionRol(usuario_id=usuario_ana.id, rol="CLIENTE"),
                    AsignacionRol(
                        usuario_id=nuevo.id,
                        rol="VENDEDOR",
                        otorgada_por=admin.id,
                    ),
                ]
            )
            await session.flush()

            # 2. Catálogo: 3 editoriales, 3 géneros y 6 autores
            editoriales = [
                Editorial(nombre="Sudamericana", pais="Argentina"),
                Editorial(nombre="Alfaguara", pais="España"),
                Editorial(nombre="Emecé", pais="Argentina"),
            ]
            session.add_all(editoriales)
            await session.flush()

            generos = [
                Genero(nombre="Novela"),
                Genero(nombre="Cuento"),
                Genero(nombre="Ensayo"),
            ]
            session.add_all(generos)
            await session.flush()

            autores = [
                Autor(nombre="Julio Cortázar", nacionalidad="Argentina"),
                Autor(nombre="Ricardo Piglia", nacionalidad="Argentina"),
                Autor(nombre="Silvina Ocampo", nacionalidad="Argentina"),
                Autor(nombre="Adolfo Bioy Casares", nacionalidad="Argentina"),
                Autor(nombre="Jorge Luis Borges", nacionalidad="Argentina"),
                Autor(nombre="Ernesto Sabato", nacionalidad="Argentina"),
            ]
            session.add_all(autores)
            await session.flush()

            sudamericana, alfaguara, emece = editoriales
            novela, cuento, _ensayo = generos
            cortazar, piglia, ocampo, bioy, borges, _sabato = autores

            # 3. Cinco libros: nacen con stock=0 y el stock se mueve con mover_stock (RN-11)
            libros_con_stock_inicial = [
                (
                    Libro(
                        isbn="978-950-00-0001-1",
                        titulo="Rayuela",
                        precio=Decimal("25000.00"),
                        stock=0,
                        editorial_id=sudamericana.id,
                        genero_id=novela.id,
                    ),
                    11,
                ),
                (
                    Libro(
                        isbn="978-950-00-0002-8",
                        titulo="Ficciones",
                        precio=Decimal("22000.00"),
                        stock=0,
                        editorial_id=emece.id,
                        genero_id=cuento.id,
                    ),
                    10,
                ),
                (
                    Libro(
                        isbn="978-950-00-0003-5",
                        titulo="Bestiario",
                        precio=Decimal("18000.00"),
                        stock=0,
                        editorial_id=sudamericana.id,
                        genero_id=cuento.id,
                    ),
                    1,
                ),
                (
                    Libro(
                        isbn="978-950-00-0004-2",
                        titulo="Respiración artificial",
                        precio=Decimal("27000.00"),
                        stock=0,
                        editorial_id=alfaguara.id,
                        genero_id=novela.id,
                    ),
                    3,
                ),
                (
                    # Sin género: la agregación es opcional.
                    # (El ISBN 978-950-00-0006-6 queda libre para los ejemplos de alta.)
                    Libro(
                        isbn="978-950-00-0007-3",
                        titulo="Antología de la literatura fantástica",
                        precio=Decimal("30000.00"),
                        stock=0,
                        editorial_id=sudamericana.id,
                    ),
                    5,
                ),
            ]
            libros = [libro for libro, _ in libros_con_stock_inicial]
            session.add_all(libros)
            await session.flush()

            rayuela, ficciones, bestiario, respiracion, antologia = libros

            autorias = [
                LibroAutor(libro_id=rayuela.id, autor_id=cortazar.id, rol="autor", orden=1),
                LibroAutor(libro_id=ficciones.id, autor_id=borges.id, rol="autor", orden=1),
                LibroAutor(libro_id=bestiario.id, autor_id=cortazar.id, rol="autor", orden=1),
                LibroAutor(libro_id=respiracion.id, autor_id=piglia.id, rol="autor", orden=1),
                LibroAutor(libro_id=antologia.id, autor_id=borges.id, rol="autor", orden=1),
                LibroAutor(libro_id=antologia.id, autor_id=ocampo.id, rol="coautor", orden=2),
                LibroAutor(libro_id=antologia.id, autor_id=bioy.id, rol="coautor", orden=3),
            ]
            session.add_all(autorias)
            await session.flush()

            repo_libros = LibroRepository(session)
            for libro, stock_inicial in libros_con_stock_inicial:
                await repo_libros.mover_stock(
                    libro,
                    stock_inicial,
                    "Stock inicial",
                    admin.id,
                )

            # 4. Clientes: Lucía (con perfil, sin usuario), Tomás (sin usuario) y Ana Paz (con usuario)
            clientes = [
                Cliente(nombre="Lucía Fernández", email="lucia@example.com"),
                Cliente(nombre="Tomás Ríos", email="tomas@example.com"),
                Cliente(nombre="Ana Paz", email="ana@example.com", usuario_id=usuario_ana.id),
            ]
            session.add_all(clientes)
            await session.flush()

            lucia, _tomas, _ana = clientes

            perfil = PerfilCliente(
                cliente_id=lucia.id,
                telefono="261-555-0101",
                direccion="San Martín 123, Mendoza",
            )
            session.add(perfil)
            await session.flush()

            # 5. Venta 1: de Lucía, registrada por vendedor@example.com, con 1 Rayuela y 2 Ficciones ($69000.00)
            renglones_a_vender = [(rayuela, 1), (ficciones, 2)]
            total = sum(
                (libro.precio * cantidad for libro, cantidad in renglones_a_vender),
                Decimal("0.00"),
            )

            venta = Venta(cliente_id=lucia.id, total=total)
            session.add(venta)
            await session.flush()

            for libro, cantidad in renglones_a_vender:
                session.add(
                    RenglonVenta(
                        venta_id=venta.id,
                        libro_id=libro.id,
                        cantidad=cantidad,
                        precio_unitario=libro.precio,
                    )
                )
                await repo_libros.mover_stock(
                    libro,
                    -cantidad,
                    "Venta",
                    vendedor.id,
                    venta_id=venta.id,
                )

            # 6. Historial de seguridad (RN-16): línea inicial con actor SISTEMA
            session.add(
                EventoSeguridad(
                    actor="SISTEMA",
                    accion="Carga de los datos iniciales",
                )
            )
            await session.flush()

            await session.commit()

            conexion = await session.connection()
            print("Filas por tabla:")
            for tabla in SQLModel.metadata.sorted_tables:
                resultado = await conexion.execute(text(f"SELECT COUNT(*) FROM {tabla.name}"))
                print(f"  {tabla.name}: {resultado.scalar_one()}")
    finally:
        if motor is not None:
            await motor.dispose()


if __name__ == "__main__":
    asyncio.run(sembrar())
