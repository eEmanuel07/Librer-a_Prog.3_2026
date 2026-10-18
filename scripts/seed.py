"""Datos iniciales de la librería.

Se corre desde la raíz del repo:

    python -m scripts.seed

Borra todos los datos del proyecto con un único
TRUNCATE ... RESTART IDENTITY CASCADE (los ids vuelven a empezar en 1),
vuelve a insertar los datos de la consigna y termina listando cuántas filas
quedaron en cada tabla. Como el TRUNCATE reinicia las secuencias, correrlo
varias veces produce exactamente el mismo resultado.

La URL de la base sale de DATABASE_URL (.env) vía get_settings(): en el
código nunca hay contraseñas ni URLs.
"""

import asyncio
import re
from decimal import Decimal

from sqlalchemy import text
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.modules.autores.models import Autor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor
from app.modules.ventas.models import RenglonVenta, Venta


def url_sin_password(url: str) -> str:
    """Enmascara la contraseña para poder imprimir la URL en consola."""
    return re.sub(r":[^:@/]+@", ":***@", url)


async def sembrar() -> None:
    ajustes = get_settings()

    print(f"Base de destino: {url_sin_password(ajustes.database_url)}")
    print("ATENCIÓN: este script borra TODOS los datos de las tablas del proyecto.")

    motor = crear_motor(ajustes.database_url, echo=ajustes.sql_echo)
    fabrica = crear_fabrica_sesiones(motor)
    try:
        async with fabrica() as session:
            # La conexión cruda se usa para el SQL directo (text(...));
            # session.execute está deprecado en SQLModel.
            conexion = await session.connection()

            tablas = ", ".join(tabla.name for tabla in SQLModel.metadata.sorted_tables)
            await conexion.execute(text(f"TRUNCATE TABLE {tablas} RESTART IDENTITY CASCADE"))

            # Los ids salen del orden de inserción (RESTART IDENTITY + flush):
            # nunca se pone un id a mano.

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
            ]
            session.add_all(autores)
            await session.flush()

            sudamericana, alfaguara, emece = editoriales
            novela, cuento, _ensayo = generos
            cortazar, piglia, ocampo, bioy, borges = autores

            libros = [
                Libro(
                    isbn="978-950-00-0001-1",
                    titulo="Rayuela",
                    precio=Decimal("25000.00"),
                    stock=12,
                    editorial_id=sudamericana.id,
                    genero_id=novela.id,
                ),
                Libro(
                    isbn="978-950-00-0002-8",
                    titulo="Ficciones",
                    precio=Decimal("18000.00"),
                    stock=8,
                    editorial_id=emece.id,
                    genero_id=cuento.id,
                ),
                Libro(
                    isbn="978-950-00-0003-5",
                    titulo="El Aleph",
                    precio=Decimal("19500.00"),
                    stock=6,
                    editorial_id=emece.id,
                    genero_id=cuento.id,
                ),
                Libro(
                    isbn="978-950-00-0004-2",
                    titulo="Respiración artificial",
                    precio=Decimal("27000.00"),
                    stock=5,
                    editorial_id=alfaguara.id,
                    genero_id=novela.id,
                ),
                Libro(
                    isbn="978-950-00-0005-9",
                    titulo="La invención de Morel",
                    precio=Decimal("16000.00"),
                    stock=10,
                    editorial_id=emece.id,
                    genero_id=novela.id,
                ),
                # Sin género: la agregación es opcional.
                # (El ISBN 978-950-00-0006-6 no se carga: lo usa el ejemplo de
                # POST /libros/ de la consigna.)
                Libro(
                    isbn="978-950-00-0007-3",
                    titulo="Antología de la literatura fantástica",
                    precio=Decimal("30000.00"),
                    stock=4,
                    editorial_id=sudamericana.id,
                ),
            ]
            session.add_all(libros)
            await session.flush()

            rayuela, ficciones, aleph, respiracion, morel, antologia = libros

            # Rol y orden en la tapa (la Antología es de varios autores).
            autorias = [
                LibroAutor(libro_id=rayuela.id, autor_id=cortazar.id, rol="autor", orden=1),
                LibroAutor(libro_id=ficciones.id, autor_id=borges.id, rol="autor", orden=1),
                LibroAutor(libro_id=aleph.id, autor_id=borges.id, rol="autor", orden=1),
                LibroAutor(libro_id=respiracion.id, autor_id=piglia.id, rol="autor", orden=1),
                LibroAutor(libro_id=morel.id, autor_id=bioy.id, rol="autor", orden=1),
                LibroAutor(libro_id=antologia.id, autor_id=borges.id, rol="autor", orden=1),
                LibroAutor(libro_id=antologia.id, autor_id=ocampo.id, rol="coautor", orden=2),
                LibroAutor(libro_id=antologia.id, autor_id=bioy.id, rol="coautor", orden=3),
            ]
            session.add_all(autorias)
            await session.flush()

            clientes = [
                Cliente(nombre="Lucía Fernández", email="lucia@example.com"),
                Cliente(nombre="Tomás Ríos", email="tomas@example.com"),
                Cliente(nombre="Camila Torres", email="camila@example.com"),
            ]
            session.add_all(clientes)
            await session.flush()

            lucia, _tomas, _camila = clientes

            # Perfil opcional (uno a uno): solo para el cliente 1.
            perfil = PerfilCliente(
                cliente_id=lucia.id,
                telefono="261-555-0101",
                direccion="San Martín 123, Mendoza",
            )
            session.add(perfil)
            await session.flush()

            # Una venta de Lucía con 2 renglones. El precio_unitario se copia
            # del libro (RN-06) y el total lo calculamos acá (RN-07).
            renglones_a_vender = [(ficciones, 1), (morel, 2)]
            total = sum(
                (libro.precio * cantidad for libro, cantidad in renglones_a_vender),
                Decimal("0.00"),
            )

            venta = Venta(cliente_id=lucia.id, total=total)
            session.add(venta)
            await session.flush()

            session.add_all(
                [
                    RenglonVenta(
                        venta_id=venta.id,
                        libro_id=libro.id,
                        cantidad=cantidad,
                        precio_unitario=libro.precio,
                    )
                    for libro, cantidad in renglones_a_vender
                ]
            )
            await session.flush()

            await session.commit()

            # Recién ahora se pide la conexión de nuevo: después del commit la
            # anterior queda devuelta al pool.
            conexion = await session.connection()
            print("Filas por tabla:")
            for tabla in SQLModel.metadata.sorted_tables:
                resultado = await conexion.execute(text(f"SELECT COUNT(*) FROM {tabla.name}"))
                print(f"  {tabla.name}: {resultado.scalar_one()}")
    finally:
        await motor.dispose()


if __name__ == "__main__":
    asyncio.run(sembrar())
