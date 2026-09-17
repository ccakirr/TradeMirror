"""create trading plans and attach new trades to active plan

Revision ID: ab51d8e3f902
Revises: 8c4e2a7d1b90
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ab51d8e3f902"
down_revision: Union[str, Sequence[str], None] = "8c4e2a7d1b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trading_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("max_risk_per_trade_pct", sa.Numeric(18, 6), nullable=False),
        sa.Column("max_daily_loss_pct", sa.Numeric(18, 6), nullable=False),
        sa.Column("max_trades_per_day", sa.Integer(), nullable=True),
        sa.Column("require_stop_loss", sa.Boolean(), nullable=False),
        sa.Column("max_open_positions", sa.Integer(), nullable=True),
        sa.Column("allowed_instruments", sa.JSON(), nullable=False),
        sa.Column("allowed_setups", sa.JSON(), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["trading_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trading_plans_account_id", "trading_plans", ["account_id"], unique=False)

    op.add_column("trades", sa.Column("plan_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_trades_plan_id_trading_plans",
        "trades",
        "trading_plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_trades_plan_id", "trades", ["plan_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_trades_plan_id", table_name="trades")
    op.drop_constraint("fk_trades_plan_id_trading_plans", "trades", type_="foreignkey")
    op.drop_column("trades", "plan_id")
    op.drop_index("ix_trading_plans_account_id", table_name="trading_plans")
    op.drop_table("trading_plans")
