"""
Data Migration Script — monolith → microservices.

Migrasi data dari database monolith (sicure_db) ke 2 database terpisah:
  - users           → auth_db
  - purchase_requisitions, pr_line_items,
    purchase_orders, grn_documents → procurement_db

Usage:
    pip install sqlalchemy psycopg2-binary
    python scripts/migrate_data.py

Prerequisite:
    - Monolith DB accessible (default: localhost:5432/sicure_db)
    - auth_db dan procurement_db sudah running (Docker Compose)
    - Expose port DB microservices di docker-compose jika perlu
"""

import os
import sys

from sqlalchemy import create_engine, text

# ── Database URLs ────────────────────────────────────────────────
MONOLITH_DB_URL = os.getenv(
    "MONOLITH_DB_URL",
    "postgresql://postgres:@localhost:5432/sicure_db",
)
AUTH_DB_URL = os.getenv(
    "AUTH_DB_URL",
    "postgresql://postgres:postgres@localhost:5433/auth_db",
)
PROCUREMENT_DB_URL = os.getenv(
    "PROCUREMENT_DB_URL",
    "postgresql://postgres:postgres@localhost:5434/procurement_db",
)


def _count(engine, table: str) -> int:
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def migrate():
    print("=" * 50)
    print("DATA MIGRATION: Monolith → Microservices")
    print("=" * 50)

    monolith = create_engine(MONOLITH_DB_URL)
    auth_db = create_engine(AUTH_DB_URL)
    proc_db = create_engine(PROCUREMENT_DB_URL)

    # ── Step 1: Users → auth_db ──────────────────────────────────
    print("\n[1/5] Migrating users → auth_db...")
    with monolith.connect() as src:
        users = src.execute(text(
            "SELECT id, email, hashed_password, full_name, role, created_at "
            "FROM users"
        )).fetchall()
    print(f"     Found {len(users)} users in monolith")

    with auth_db.connect() as dst:
        for u in users:
            dst.execute(text("""
                INSERT INTO users (id, email, hashed_password, full_name, role, created_at)
                VALUES (:id, :email, :hashed_password, :full_name, :role, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": u[0], "email": u[1], "hashed_password": u[2],
                "full_name": u[3], "role": u[4], "created_at": u[5],
            })
        dst.commit()
    print(f"     Migrated {len(users)} users")

    # ── Step 2: Purchase Requisitions → procurement_db ───────────
    print("\n[2/5] Migrating purchase_requisitions → procurement_db...")
    with monolith.connect() as src:
        prs = src.execute(text(
            "SELECT id, pr_number, requester_id, title, justification, "
            "status, total_amount, created_at, updated_at, approval_note "
            "FROM purchase_requisitions"
        )).fetchall()
    print(f"     Found {len(prs)} PRs in monolith")

    with proc_db.connect() as dst:
        for pr in prs:
            dst.execute(text("""
                INSERT INTO purchase_requisitions
                    (id, pr_number, requester_id, title, justification,
                     status, total_amount, created_at, updated_at, approval_note)
                VALUES (:id, :pr_number, :requester_id, :title, :justification,
                        :status, :total_amount, :created_at, :updated_at, :approval_note)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": pr[0], "pr_number": pr[1], "requester_id": pr[2],
                "title": pr[3], "justification": pr[4], "status": pr[5],
                "total_amount": pr[6], "created_at": pr[7],
                "updated_at": pr[8], "approval_note": pr[9],
            })
        dst.commit()
    print(f"     Migrated {len(prs)} PRs")

    # ── Step 3: PR Line Items → procurement_db ───────────────────
    print("\n[3/5] Migrating pr_line_items → procurement_db...")
    with monolith.connect() as src:
        items = src.execute(text(
            "SELECT id, pr_id, item_name, quantity, unit_of_measure, "
            "estimated_unit_price, subtotal "
            "FROM pr_line_items"
        )).fetchall()
    print(f"     Found {len(items)} line items in monolith")

    with proc_db.connect() as dst:
        for it in items:
            dst.execute(text("""
                INSERT INTO pr_line_items
                    (id, pr_id, item_name, quantity, unit_of_measure,
                     estimated_unit_price, subtotal)
                VALUES (:id, :pr_id, :item_name, :quantity, :uom,
                        :est_price, :subtotal)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": it[0], "pr_id": it[1], "item_name": it[2],
                "quantity": it[3], "uom": it[4],
                "est_price": it[5], "subtotal": it[6],
            })
        dst.commit()
    print(f"     Migrated {len(items)} line items")

    # ── Step 4: Purchase Orders → procurement_db ─────────────────
    print("\n[4/5] Migrating purchase_orders → procurement_db...")
    with monolith.connect() as src:
        pos = src.execute(text(
            "SELECT id, po_number, pr_id, issued_by, issued_at, allocated_budget "
            "FROM purchase_orders"
        )).fetchall()
    print(f"     Found {len(pos)} POs in monolith")

    with proc_db.connect() as dst:
        for po in pos:
            dst.execute(text("""
                INSERT INTO purchase_orders
                    (id, po_number, pr_id, issued_by, issued_at, allocated_budget)
                VALUES (:id, :po_number, :pr_id, :issued_by, :issued_at, :budget)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": po[0], "po_number": po[1], "pr_id": po[2],
                "issued_by": po[3], "issued_at": po[4], "budget": po[5],
            })
        dst.commit()
    print(f"     Migrated {len(pos)} POs")

    # ── Step 5: GRN Documents → procurement_db ───────────────────
    print("\n[5/5] Migrating grn_documents → procurement_db...")
    with monolith.connect() as src:
        grns = src.execute(text(
            "SELECT id, po_id, requester_id, receipt_url, "
            "commercial_invoice_url, goods_photo_url, submitted_at, "
            "verification_note "
            "FROM grn_documents"
        )).fetchall()
    print(f"     Found {len(grns)} GRN documents in monolith")

    with proc_db.connect() as dst:
        for g in grns:
            dst.execute(text("""
                INSERT INTO grn_documents
                    (id, po_id, requester_id, receipt_url,
                     commercial_invoice_url, goods_photo_url,
                     submitted_at, verification_note)
                VALUES (:id, :po_id, :requester_id, :receipt_url,
                        :invoice_url, :photo_url, :submitted_at, :note)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": g[0], "po_id": g[1], "requester_id": g[2],
                "receipt_url": g[3], "invoice_url": g[4],
                "photo_url": g[5], "submitted_at": g[6], "note": g[7],
            })
        dst.commit()
    print(f"     Migrated {len(grns)} GRN documents")

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("MIGRATION COMPLETE!")
    print(f"  auth_db:        {_count(auth_db, 'users')} users")
    print(f"  procurement_db: {_count(proc_db, 'purchase_requisitions')} PRs, "
          f"{_count(proc_db, 'pr_line_items')} line items, "
          f"{_count(proc_db, 'purchase_orders')} POs, "
          f"{_count(proc_db, 'grn_documents')} GRN docs")
    print("=" * 50)


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\nMigration failed: {e}")
        print("Pastikan semua database accessible dan tabel sudah dibuat.")
        sys.exit(1)
