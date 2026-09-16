"""widen price precision for exchange-grade instruments

Numeric(18, 4) could not hold what real venues quote: 398 of Binance's 1372
tradable spot pairs tick finer than 0.0001 (down to 1e-8), and even BTCUSDT's
lot step is 0.00001. Widening to Numeric(28, 10) keeps 18 digits ahead of the
point while covering every step in the catalog.

Widening a numeric is lossless, so the downgrade is the only risky direction:
it will fail on rows that already carry more than four decimals.

Revision ID: c3a71f2b8d04
Revises: e46b83f9462e
Create Date: 2026-09-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a71f2b8d04'
down_revision: Union[str, Sequence[str], None] = 'e46b83f9462e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


WIDE = sa.Numeric(28, 10)
NARROW = sa.Numeric(18, 4)

COLUMNS: tuple[tuple[str, str, bool], ...] = (
    ("trading_accounts", "initial_balance", False),
    ("trading_accounts", "current_balance", False),
    ("trades", "entry_price", False),
    ("trades", "exit_price", True),
    ("trades", "position_size", False),
    ("trades", "stop_loss", True),
    ("trades", "take_profit", True),
    ("trades", "pnl", True),
)


def upgrade() -> None:
    """Upgrade schema."""
    for table, column, nullable in COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=NARROW,
            type_=WIDE,
            existing_nullable=nullable,
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table, column, nullable in COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=WIDE,
            type_=NARROW,
            existing_nullable=nullable,
        )
