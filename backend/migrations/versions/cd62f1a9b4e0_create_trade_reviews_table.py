"""create trade reviews table

Revision ID: cd62f1a9b4e0
Revises: ab51d8e3f902
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cd62f1a9b4e0"
down_revision: Union[str, Sequence[str], None] = "ab51d8e3f902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trade_reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("trade_id", sa.UUID(), nullable=False),
        sa.Column("plan_adherence", sa.String(length=32), nullable=False),
        sa.Column("setup_followed", sa.Boolean(), nullable=False),
        sa.Column("pre_trade_emotion", sa.String(length=64), nullable=True),
        sa.Column("post_trade_emotion", sa.String(length=64), nullable=True),
        sa.Column("mistake_tags", sa.JSON(), nullable=False),
        sa.Column("lesson", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["trade_id"], ["trades.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trade_id"),
    )
    op.create_index("ix_trade_reviews_trade_id", "trade_reviews", ["trade_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_trade_reviews_trade_id", table_name="trade_reviews")
    op.drop_table("trade_reviews")
