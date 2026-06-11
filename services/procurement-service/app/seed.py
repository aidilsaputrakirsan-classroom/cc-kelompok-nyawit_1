import asyncio
import os
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import engine, async_session
from app.models.enums import PRStatus
from app.models.purchase_requisition import PurchaseRequisition
from app.models.pr_line_item import PRLineItem
from app.models.purchase_order import PurchaseOrder
from app.models.grn_document import GRNDocument

SEED_PRS = [
    {
        "requester_idx": 0,
        "title": "Pengadaan Server Rack untuk Data Center",
        "justification": "Kapasitas server rack di data center sudah penuh. Diperlukan tambahan rack untuk menampung server baru yang akan digunakan untuk proyek migrasi cloud.",
        "target_status": PRStatus.SUBMITTED,
        "items": [
            ("Server Rack 42U", 2, "unit", 15_000_000),
            ("Patch Panel Cat6 24-Port", 4, "pcs", 850_000),
            ("Cable Management Panel 1U", 8, "pcs", 250_000),
            ("PDU Rack-Mount 16A", 2, "unit", 3_500_000),
        ],
    },
    {
        "requester_idx": 1,
        "title": "Pembelian Lisensi Software Development Tools",
        "justification": "Tim development membutuhkan lisensi IDE dan tools kolaborasi untuk meningkatkan produktivitas. Lisensi lama sudah expired bulan lalu.",
        "target_status": PRStatus.SUBMITTED,
        "items": [
            ("JetBrains All Products Pack (Annual)", 10, "lisensi", 3_200_000),
            ("GitHub Enterprise Cloud (Annual)", 1, "lisensi", 45_000_000),
            ("Figma Professional (Annual)", 5, "lisensi", 2_800_000),
        ],
    },
    {
        "requester_idx": 0,
        "title": "Upgrade RAM dan SSD untuk Workstation Engineering",
        "justification": "Workstation tim engineering sering mengalami lag saat menjalankan Docker containers dan kompilasi project. Upgrade hardware diperlukan untuk efisiensi kerja.",
        "target_status": PRStatus.APPROVED,
        "approval_note": "Disetujui. Spesifikasi sudah sesuai kebutuhan tim engineering. Pastikan kompatibilitas dengan motherboard yang ada.",
        "items": [
            ("DDR5 RAM 32GB Kit (2x16GB)", 8, "kit", 2_100_000),
            ("NVMe SSD 1TB Gen4", 8, "pcs", 1_750_000),
            ("Thermal Paste Noctua NT-H2", 8, "tube", 150_000),
        ],
    },
    {
        "requester_idx": 2,
        "title": "Pembelian Drone untuk Monitoring Infrastruktur",
        "justification": "Menggunakan drone untuk inspeksi visual tower telekomunikasi dan kabel fiber optik di area terpencil.",
        "target_status": PRStatus.REJECTED,
        "approval_note": "Ditolak. Budget tahun ini sudah dialokasikan untuk prioritas lain. Silakan ajukan kembali di Q1 tahun depan. Pertimbangkan juga opsi sewa drone sebagai alternatif.",
        "items": [
            ("DJI Matrice 350 RTK", 1, "unit", 85_000_000),
            ("DJI Zenmuse H20T Camera", 1, "unit", 65_000_000),
            ("Extra Battery TB65", 4, "pcs", 5_500_000),
            ("DJI Pilot 2 License", 2, "lisensi", 3_000_000),
        ],
    },
    {
        "requester_idx": 1,
        "title": "Pengadaan Perangkat Jaringan untuk Kantor Baru",
        "justification": "Kantor cabang baru membutuhkan infrastruktur jaringan lengkap termasuk switch managed, access point, dan firewall untuk mendukung 50 karyawan.",
        "target_status": PRStatus.PO_ISSUED,
        "approval_note": "Disetujui. Spesifikasi jaringan sudah di-review oleh tim IT. Vendor yang direkomendasikan: PT Solusi Infrastruktur Digital.",
        "items": [
            ("Cisco Catalyst 9200L-48P Switch", 2, "unit", 28_000_000),
            ("Ubiquiti UniFi U6 Pro Access Point", 6, "unit", 3_200_000),
            ("FortiGate 60F Firewall", 1, "unit", 18_500_000),
            ("Cat6A UTP Cable 305m Box", 3, "box", 4_200_000),
            ("RJ45 Cat6A Connector (100pcs)", 2, "pack", 650_000),
        ],
    },
    {
        "requester_idx": 2,
        "title": "Pembelian Laptop untuk Tim Data Science",
        "justification": "Tim data science baru dibentuk dan membutuhkan laptop dengan GPU dedicated untuk training model machine learning dan analisis big data.",
        "target_status": PRStatus.DOC_SUBMITTED,
        "approval_note": "Disetujui. Spesifikasi laptop sudah sesuai untuk kebutuhan ML/AI workload. Pilih vendor dengan garansi on-site 3 tahun.",
        "items": [
            ("Lenovo ThinkPad P16 Gen2 (i9/RTX 4080)", 3, "unit", 42_000_000),
            ("Lenovo Thunderbolt 4 Dock", 3, "unit", 5_500_000),
            ("LG UltraFine 27\" 4K Monitor", 3, "unit", 7_800_000),
        ],
    },
    {
        "requester_idx": 0,
        "title": "Pengadaan UPS untuk Server Room",
        "justification": "Server room membutuhkan UPS tambahan untuk menjamin uptime 99.99%. UPS lama sudah berusia 5 tahun dan kapasitas baterainya menurun signifikan.",
        "target_status": PRStatus.VERIFIED,
        "approval_note": "Disetujui. Kebutuhan UPS sangat kritis untuk menjaga kelangsungan operasional server. Prioritas tinggi.",
        "verification_note": "Barang sudah diterima lengkap dan sesuai spesifikasi. Instalasi sudah dilakukan oleh teknisi vendor. Garansi 3 tahun terdaftar.",
        "items": [
            ("APC Smart-UPS SRT 5000VA", 2, "unit", 35_000_000),
            ("APC Battery Pack SRT192BP", 2, "unit", 18_000_000),
            ("APC Network Management Card 3", 2, "pcs", 4_500_000),
        ],
    },
    {
        "requester_idx": 1,
        "title": "Pembelian Perangkat IoT untuk Smart Office",
        "justification": "Implementasi smart office menggunakan sensor IoT untuk monitoring suhu, kelembaban, dan occupancy ruangan. Proyek ini bagian dari inisiatif green building.",
        "target_status": PRStatus.CLOSED,
        "approval_note": "Disetujui. Proyek smart office sudah masuk dalam roadmap IT tahun ini. Budget sudah dialokasikan di CAPEX Q2.",
        "verification_note": "Semua perangkat IoT sudah diterima, diuji, dan terhubung ke dashboard monitoring. Sistem berjalan normal. Proses procurement dinyatakan selesai.",
        "items": [
            ("Raspberry Pi 4 Model B 8GB", 10, "unit", 1_200_000),
            ("DHT22 Temperature & Humidity Sensor", 20, "pcs", 85_000),
            ("PIR Motion Sensor HC-SR501", 15, "pcs", 35_000),
            ("LoRa Gateway RAK7268", 2, "unit", 4_500_000),
            ("PoE Injector 48V", 10, "pcs", 250_000),
        ],
    },
    {
        "requester_idx": 2,
        "title": "Pengadaan Peralatan Cybersecurity Lab",
        "justification": "Divisi keamanan informasi membutuhkan lab khusus untuk penetration testing dan security audit. Peralatan ini akan digunakan untuk red team exercise internal.",
        "target_status": PRStatus.SUBMITTED,
        "items": [
            ("Hak5 WiFi Pineapple Mark VII", 2, "unit", 4_500_000),
            ("Flipper Zero", 3, "unit", 3_200_000),
            ("Proxmark3 RDV4", 2, "unit", 5_800_000),
            ("Alfa AWUS036ACH WiFi Adapter", 5, "pcs", 750_000),
            ("Rubber Ducky USB", 5, "pcs", 1_200_000),
        ],
    },
    {
        "requester_idx": 0,
        "title": "Pembelian Lisensi Cloud Platform",
        "justification": "Migrasi infrastruktur ke cloud membutuhkan reserved instances AWS dan lisensi monitoring tools untuk memastikan performa dan cost optimization.",
        "target_status": PRStatus.CLOSED,
        "approval_note": "Disetujui. Migrasi cloud adalah prioritas strategis. Pastikan reserved instances sesuai sizing yang sudah direkomendasikan oleh cloud architect.",
        "verification_note": "Semua lisensi sudah aktif dan terkonfigurasi. Dashboard monitoring Datadog sudah menampilkan metrics dari seluruh environment. Procurement selesai.",
        "items": [
            ("AWS Reserved Instance c6i.2xlarge (1yr)", 5, "unit", 48_000_000),
            ("Datadog Pro Plan (Annual)", 1, "lisensi", 62_000_000),
            ("HashiCorp Terraform Cloud Business", 1, "lisensi", 28_000_000),
        ],
    },
    {
        "requester_idx": 2,
        "title": "Pengadaan Perangkat Video Conference",
        "justification": "Ruang meeting perlu di-upgrade dengan perangkat video conference berkualitas tinggi untuk mendukung hybrid working dan meeting dengan klien internasional.",
        "target_status": PRStatus.PO_ISSUED,
        "approval_note": "Disetujui. Upgrade fasilitas meeting room sudah lama direncanakan. Pilih perangkat yang kompatibel dengan Microsoft Teams dan Zoom.",
        "items": [
            ("Poly Studio X50 Video Bar", 3, "unit", 22_000_000),
            ("Poly TC10 Touch Controller", 3, "unit", 8_500_000),
            ("Samsung 75\" QLED 4K Display", 3, "unit", 18_000_000),
            ("Shure MXA920 Ceiling Mic", 3, "unit", 15_000_000),
        ],
    },
]


async def seed_procurement_data(db: AsyncSession):
    # Ensure tables are created first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Check if there is already PR data
    result = await db.execute(select(PurchaseRequisition).limit(1))
    if result.scalar_one_or_none() is not None:
        print("  - Procurement database already has data, skipping seed.")
        return

    now = datetime.now(timezone.utc)
    pr_counter = 0

    for pr_data in SEED_PRS:
        pr_counter += 1
        # Map requester_idx to user IDs:
        # Admin is User ID 1, requesters are 2, 3, 4
        requester_id = pr_data["requester_idx"] + 2
        target = pr_data["target_status"]

        pr_number = f"PR-{now.strftime('%Y%m%d')}-{pr_counter:06d}"
        total = sum(qty * price for _, qty, _, price in pr_data["items"])

        pr = PurchaseRequisition(
            pr_number=pr_number,
            requester_id=requester_id,
            title=pr_data["title"],
            justification=pr_data["justification"],
            status=PRStatus.SUBMITTED,
            total_amount=total,
        )
        db.add(pr)
        await db.flush()

        for item_name, qty, uom, unit_price in pr_data["items"]:
            item = PRLineItem(
                pr_id=pr.id,
                item_name=item_name,
                quantity=qty,
                unit_of_measure=uom,
                estimated_unit_price=unit_price,
                subtotal=qty * unit_price,
            )
            db.add(item)

        await db.flush()

        # Advance PR status
        po = None
        grn = None

        if target in (
            PRStatus.APPROVED, PRStatus.PO_ISSUED,
            PRStatus.DOC_SUBMITTED, PRStatus.VERIFIED, PRStatus.CLOSED,
        ):
            pr.status = PRStatus.APPROVED
            pr.approval_note = pr_data.get("approval_note", "Disetujui.")
            await db.flush()

        if target == PRStatus.REJECTED:
            pr.status = PRStatus.REJECTED
            pr.approval_note = pr_data.get("approval_note", "Ditolak.")
            await db.flush()

        if target in (
            PRStatus.PO_ISSUED, PRStatus.DOC_SUBMITTED,
            PRStatus.VERIFIED, PRStatus.CLOSED,
        ):
            po_number = f"PO-{now.strftime('%Y%m%d')}-{pr_counter:06d}"
            # Admin user ID = 1
            po = PurchaseOrder(
                po_number=po_number,
                pr_id=pr.id,
                issued_by=1,
                allocated_budget=total,
            )
            db.add(po)
            pr.status = PRStatus.PO_ISSUED
            await db.flush()

        if target in (
            PRStatus.DOC_SUBMITTED, PRStatus.VERIFIED, PRStatus.CLOSED,
        ):
            grn = GRNDocument(
                po_id=po.id,
                requester_id=requester_id,
                receipt_url=f"uploads/{po.id}/dummy_receipt.pdf",
                commercial_invoice_url=f"uploads/{po.id}/dummy_invoice.pdf",
                goods_photo_url=f"uploads/{po.id}/dummy_photo.jpg",
            )
            db.add(grn)
            pr.status = PRStatus.DOC_SUBMITTED
            await db.flush()

        if target in (PRStatus.VERIFIED, PRStatus.CLOSED):
            grn.verification_note = pr_data.get(
                "verification_note",
                "Dokumen sudah diverifikasi dan barang sesuai."
            )
            pr.status = PRStatus.VERIFIED
            await db.flush()

        if target == PRStatus.CLOSED:
            pr.status = PRStatus.CLOSED
            await db.flush()

        print(f"  ✓ PR #{pr_counter}: {pr.pr_number} | Status: {pr.status} | Total: Rp {total:,.0f}")

    await db.commit()


async def main():
    print("🔄 Starting Procurement Service database seeding...")
    async with async_session() as session:
        await seed_procurement_data(session)
    print("✅ Procurement Service database seeding completed.")


if __name__ == "__main__":
    asyncio.run(main())
