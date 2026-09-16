"""create account risk profiles table

Revision ID: 8c4e2a7d1b90
Revises: 7b2d1f4c9a81
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c4e2a7d1b90"
down_revision: Union[str, Sequence[str], None] = "7b2d1f4c9a81"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trading_account_risk_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("instrument", sa.String(length=16), nullable=False),
        sa.Column(
            "risk_per_trade_pct",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
        ),
        sa.Column(
            "trades_per_month",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
        ),
        sa.Column(
            "avg_win_hold_days",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
        ),
        sa.Column(
            "avg_loss_hold_days",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
        ),
        sa.Column(
            "diversification",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
        ),
        sa.Column(
            "follows_plan",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
        ),
        sa.Column(
            "position_sizing_discipline",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["trading_accounts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id"),
    )
    op.create_index(
        "ix_trading_account_risk_profiles_account_id",
        "trading_account_risk_profiles",
        ["account_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_trading_account_risk_profiles_account_id",
        table_name="trading_account_risk_profiles",
    )
    op.drop_table("trading_account_risk_profiles")
