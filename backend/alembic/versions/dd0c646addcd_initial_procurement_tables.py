"""initial_procurement_tables

Revision ID: dd0c646addcd
Revises:
Create Date: 2026-04-15 11:30:58.190527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dd0c646addcd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all procurement tables."""

    # ── users ──────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="requester"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── purchase_requisitions ──────────────────────────────────────
    op.create_table(
        "purchase_requisitions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "pr_number",
            sa.String(30),
            nullable=False,
            comment="Auto-generated PR number, e.g. PR-20260415-0001",
        ),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="SUBMITTED"),
        sa.Column("total_amount", sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("approval_note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pr_number"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_purchase_requisitions_pr_number", "purchase_requisitions", ["pr_number"])
    op.create_index("ix_purchase_requisitions_requester_id", "purchase_requisitions", ["requester_id"])
    op.create_index("ix_purchase_requisitions_status", "purchase_requisitions", ["status"])

    # ── pr_line_items ──────────────────────────────────────────────
    op.create_table(
        "pr_line_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pr_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "unit_of_measure",
            sa.String(50),
            nullable=False,
            comment="e.g. pcs, kg, liter, box, unit",
        ),
        sa.Column("estimated_unit_price", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            comment="quantity * estimated_unit_price",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["pr_id"], ["purchase_requisitions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_pr_line_items_pr_id", "pr_line_items", ["pr_id"])

    # ── purchase_orders ────────────────────────────────────────────
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "po_number",
            sa.String(30),
            nullable=False,
            comment="Auto-generated PO number, e.g. PO-20260415-0001",
        ),
        sa.Column("pr_id", sa.Integer(), nullable=False),
        sa.Column("issued_by", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("allocated_budget", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("po_number"),
        sa.UniqueConstraint("pr_id"),
        sa.ForeignKeyConstraint(["pr_id"], ["purchase_requisitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["issued_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_purchase_orders_po_number", "purchase_orders", ["po_number"])
    op.create_index("ix_purchase_orders_pr_id", "purchase_orders", ["pr_id"])
    op.create_index("ix_purchase_orders_issued_by", "purchase_orders", ["issued_by"])

    # ── grn_documents ──────────────────────────────────────────────
    op.create_table(
        "grn_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("po_id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("receipt_url", sa.String(500), nullable=False),
        sa.Column("commercial_invoice_url", sa.String(500), nullable=False),
        sa.Column("goods_photo_url", sa.String(500), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("po_id"),
        sa.ForeignKeyConstraint(["po_id"], ["purchase_orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_grn_documents_po_id", "grn_documents", ["po_id"])
    op.create_index("ix_grn_documents_requester_id", "grn_documents", ["requester_id"])


def downgrade() -> None:
    """Drop all procurement tables in reverse dependency order."""
    op.drop_table("grn_documents")
    op.drop_table("purchase_orders")
    op.drop_table("pr_line_items")
    op.drop_table("purchase_requisitions")
    op.drop_table("users")
