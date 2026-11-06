"""disparador de solo agregado en movimiento_stock

Revision ID: 314ce2736bff
Revises: 4a775b04f730
Create Date: 2026-11-06 01:21:36.657093

LEÍDA ANTES DE APLICARLA (Ej. 2). ESCRITA A MANO: la comparación automática de
Alembic (--autogenerate) no ve funciones ni disparadores, así que nunca la habría
generado, y alembic check no avisa si falta.

Instala el disparador de sólo agregado de movimiento_stock (RN-12, Ej. 7): la
base rechaza cualquier UPDATE o DELETE sobre esa tabla, venga de donde venga
(la aplicación, psql u otra herramienta). Un movimiento mal cargado no se
corrige: se compensa con otro movimiento de signo contrario.

Decisiones:
* BEFORE ... FOR EACH ROW: corta la operación antes de que toque la fila.
* ERRCODE restrict_violation (SQLSTATE 23001, de la clase 23, violación de
  integridad): asyncpg lo levanta como IntegrityError, así que si la aplicación
  alguna vez lo intentara, el UnitOfWork lo traduce a 409 con mensaje propio y
  no termina en un 500 (RN-16).
* TRUNCATE no se bloquea a propósito: no es UPDATE ni DELETE, no dispara los
  disparadores por fila, y seed.py lo usa para dejar la base en su estado inicial.
* El downgrade borra el disparador y después la función, en ese orden, porque
  el disparador depende de la función.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '314ce2736bff'
down_revision: Union[str, Sequence[str], None] = '4a775b04f730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE FUNCTION movimiento_stock_solo_agregado() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'movimiento_stock es de solo agregado: no admite %', TG_OP
                USING ERRCODE = 'restrict_violation',
                      HINT = 'Para corregir un movimiento, registrá otro que lo compense.';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_movimiento_stock_solo_agregado
        BEFORE UPDATE OR DELETE ON movimiento_stock
        FOR EACH ROW EXECUTE FUNCTION movimiento_stock_solo_agregado()
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER trg_movimiento_stock_solo_agregado ON movimiento_stock")
    op.execute("DROP FUNCTION movimiento_stock_solo_agregado()")
