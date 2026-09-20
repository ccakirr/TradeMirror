"""align one-to-one relationships with SQLAlchemy unique indexes

Revision ID: de73a4b6c812
Revises: cd62f1a9b4e0
"""

from typing import Sequence, Union

from alembic import op


revision: str = "de73a4b6c812"
down_revision: Union[str, Sequence[str], None] = "cd62f1a9b4e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "trade_reviews_trade_id_key",
        "trade_reviews",
        type_="unique",
    )
    op.drop_constraint(
        "trading_account_risk_profiles_account_id_key",
        "trading_account_risk_profiles",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "trade_reviews_trade_id_key",
        "trade_reviews",
        ["trade_id"],
    )
    op.create_unique_constraint(
        "trading_account_risk_profiles_account_id_key",
        "trading_account_risk_profiles",
        ["account_id"],
    )
