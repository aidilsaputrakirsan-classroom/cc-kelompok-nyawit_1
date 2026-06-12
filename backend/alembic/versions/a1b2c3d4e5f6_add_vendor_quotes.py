"""add_vendor_quotes

Revision ID: a1b2c3d4e5f6
Revises: 79d612cfd7c5
Create Date: 2026-06-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "79d612cfd7c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create vendor_quotes table and add selected_vendor_quote_id to purchase_orders."""

    # ── vendor_quotes ──────────────────────────────────────────────
    op.create_table(
        "vendor_quotes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pr_id", sa.Integer(), nullable=False),
        sa.Column("vendor_name", sa.String(255), nullable=False),
        sa.Column("vendor_contact", sa.String(255), nullable=False),
        sa.Column("quoted_price", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("survey_date", sa.Date(), nullable=False),
        sa.Column("survey_evidence_url", sa.String(500), nullable=False),
        sa.Column("is_recommended", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["pr_id"], ["purchase_requisitions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_vendor_quotes_pr_id", "vendor_quotes", ["pr_id"])

    # ── purchase_orders.selected_vendor_quote_id ───────────────────
    op.add_column(
        "purchase_orders",
        sa.Column("selected_vendor_quote_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_purchase_orders_selected_vendor_quote_id",
        "purchase_orders",
        ["selected_vendor_quote_id"],
    )
    op.create_foreign_key(
        "fk_purchase_orders_selected_vendor_quote_id",
        "purchase_orders",
        "vendor_quotes",
        ["selected_vendor_quote_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Reverse the vendor_quotes migration."""
    op.drop_constraint(
        "fk_purchase_orders_selected_vendor_quote_id",
        "purchase_orders",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_purchase_orders_selected_vendor_quote_id",
        "purchase_orders",
    )
    op.drop_column("purchase_orders", "selected_vendor_quote_id")
    op.drop_index("ix_vendor_quotes_pr_id", "vendor_quotes")
    op.drop_table("vendor_quotes")
