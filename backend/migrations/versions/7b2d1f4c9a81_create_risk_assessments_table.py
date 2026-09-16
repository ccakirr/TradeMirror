"""create risk assessments table

Revision ID: 7b2d1f4c9a81
Revises: c3a71f2b8d04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b2d1f4c9a81"
down_revision: Union[str, Sequence[str], None] = "c3a71f2b8d04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("trade_id", sa.UUID(), nullable=False),
        sa.Column("stage", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Numeric(precision=18, scale=10), nullable=False),
        sa.Column("risk_class", sa.String(length=16), nullable=False),
        sa.Column(
            "threshold", sa.Numeric(precision=18, scale=10), nullable=False
        ),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["trade_id"], ["trades.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_assessments_trade_id",
        "risk_assessments",
        ["trade_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_risk_assessments_trade_id", table_name="risk_assessments"
    )
    op.drop_table("risk_assessments")
