import { useEffect, useState, type FormEvent } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import api from "../../services/api";
import { useToast } from "../../contexts/ToastContext";
import { useProcurement } from "../../contexts/ProcurementContext";
import StatusBadge from "../../components/StatusBadge";
import type {
  PurchaseRequisition,
  PurchaseOrder,
  GRNDocument,
  APIResponse,
  PRStatus,
} from "../../types";
import { formatDateID, formatDateTimeID } from "../../utils/formatHelpers";

/** Ordered status timeline */
const STATUS_TIMELINE: { key: PRStatus; label: string }[] = [
  { key: "SUBMITTED", label: "Submitted" },
  { key: "APPROVED", label: "Approved" },
  { key: "PO_ISSUED", label: "PO Issued" },
  { key: "DOC_SUBMITTED", label: "Doc Submitted" },
  { key: "VERIFIED", label: "Verified" },
  { key: "CLOSED", label: "Closed" },
];

function getTimelineIndex(status: PRStatus): number {
  if (status === "REJECTED") return 1; // stops at the approval decision stage
  const idx = STATUS_TIMELINE.findIndex((s) => s.key === status);
  return idx >= 0 ? idx : 0;
}

export default function RequesterPRDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { invalidate } = useProcurement();

  const [pr, setPr] = useState<PurchaseRequisition | null>(null);
  const [po, setPo] = useState<PurchaseOrder | null>(null);
  const [grn, setGrn] = useState<GRNDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Reason shown when a previously submitted GRN was returned by the admin
  const [grnReturnNote, setGrnReturnNote] = useState<string | null>(null);

  // GRN upload state
  const [showGrnModal, setShowGrnModal] = useState(false);
  const [invoiceFile, setInvoiceFile] = useState<File | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Delete confirmation state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api
      .get<APIResponse<PurchaseRequisition>>(`/requisitions/${id}`)
      .then((res) => {
        setPr(res.data.data);
        const prData = res.data.data;
        if (
          ["PO_ISSUED", "DOC_SUBMITTED", "VERIFIED", "CLOSED"].includes(
            prData.status
          )
        ) {
          return api
            .get<APIResponse<PurchaseOrder>>(`/purchase-orders/${prData.id}/my-po`)
            .then((poRes) => {
              if (poRes.data.success && poRes.data.data) {
                setPo(poRes.data.data);
                // If PR is back at PO_ISSUED, a returned GRN may carry a reason
                if (prData.status === "PO_ISSUED") {
                  return api
                    .get<APIResponse<GRNDocument>>(
                      `/grn/by-po/${poRes.data.data.id}`
                    )
                    .then((g) => {
                      if (g.data.data?.verification_note) {
                        setGrnReturnNote(g.data.data.verification_note);
                      }
                    })
                    .catch(() => {
                      // No GRN yet — first-time submission, nothing to show
                    });
                }
                // If DOC_SUBMITTED, VERIFIED, or CLOSED, fetch the GRN details
                if (["DOC_SUBMITTED", "VERIFIED", "CLOSED"].includes(prData.status)) {
                  return api
                    .get<APIResponse<GRNDocument>>(
                      `/grn/by-po/${poRes.data.data.id}`
                    )
                    .then((g) => {
                      if (g.data.data) {
                        setGrn(g.data.data);
                      }
                    })
                    .catch(() => {
                      // GRN not found - leave as null
                    });
                }
              }
            })
            .catch(() => {
              // PO may not exist yet or other error - that's OK
            });
        }
      })
      .catch(() => setError("Gagal memuat detail PR."))
      .finally(() => setLoading(false));
  }, [id]);

  const handleGrnSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!invoiceFile || !photoFile) {
      showToast("error", "Kedua file (invoice & foto barang) wajib diupload.");
      return;
    }
    if (!po) {
      showToast("error", "Data PO tidak ditemukan.");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("commercial_invoice", invoiceFile);
    formData.append("goods_photo", photoFile);

    try {
      await api.post(`/grn/${po.id}/submit-doc`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      showToast("success", "Dokumen GRN berhasil di-submit!");
      setShowGrnModal(false);
      setInvoiceFile(null);
      setPhotoFile(null);
      setGrnReturnNote(null);
      // Refresh PR data
      const res = await api.get<APIResponse<PurchaseRequisition>>(
        `/requisitions/${id}`
      );
      setPr(res.data.data);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Gagal submit dokumen GRN.";
      showToast("error", msg);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.delete(`/requisitions/${id}`);
      showToast("success", "Purchase Requisition berhasil dibatalkan dan dihapus.");
      invalidate();
      navigate("/requester/dashboard");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Gagal membatalkan Purchase Requisition.";
      showToast("error", msg);
    } finally {
      setDeleting(false);
      setShowDeleteModal(false);
    }
  };

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(val);

  const formatDate = (dateStr: string) => formatDateTimeID(dateStr);

  if (loading) return <p className="text-muted">Memuat detail PR...</p>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!pr) return <div className="alert alert-error">PR tidak ditemukan.</div>;

  const currentIdx = getTimelineIndex(pr.status);
  const isRejected = pr.status === "REJECTED";

  return (
    <div className="page">
      <div className="page-header">
        <h2>Detail PR: {pr.pr_number}</h2>
        <Link to="/requester/dashboard" className="btn-back">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          Kembali 
        </Link>
      </div>

      {/* Status Timeline */}
      <div className="timeline-card">
        <div className="timeline-header">
          <h3>Status Timeline</h3>
          <StatusBadge status={pr.status} />
        </div>
        <div className="status-timeline">
          {STATUS_TIMELINE.map((step, idx) => {
            let state: "done" | "active" | "pending" = "pending";
            if (isRejected) {
              if (idx === 0) state = "done";
              else if (idx === 1) state = "active";
            } else {
              if (idx < currentIdx) state = "done";
              else if (idx === currentIdx) state = "active";
            }

            const stepNumber = idx + 1;

            return (
              <div
                key={step.key}
                className={`timeline-step timeline-${state}${isRejected && idx === 1 ? " timeline-rejected" : ""}`}
              >
                <div className="timeline-dot">
                  {state === "done" && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                  {state === "active" && !isRejected && (
                    <span className="timeline-dot-pulse" />
                  )}
                  {state === "active" && isRejected && idx === 1 && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  )}
                  {state === "pending" && (
                    <span className="timeline-dot-number">{stepNumber}</span>
                  )}
                </div>
                <span className="timeline-label">{step.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* PR Info */}
      <div className="detail-card">
        <h3>Informasi PR</h3>
        <div className="detail-grid">
          <div className="detail-item">
            <span className="detail-label">No. PR</span>
            <span className="detail-value font-mono">{pr.pr_number}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Judul</span>
            <span className="detail-value">{pr.title}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Status</span>
            <span className="detail-value">
              <StatusBadge status={pr.status} />
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Total</span>
            <span className="detail-value font-mono">
              {formatCurrency(pr.total_amount)}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Tanggal Dibuat</span>
            <span className="detail-value">{formatDate(pr.created_at)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Terakhir Diupdate</span>
            <span className="detail-value">{formatDate(pr.updated_at)}</span>
          </div>
        </div>
        {pr.justification && (
          <div className="detail-section">
            <span className="detail-label">Justifikasi</span>
            <p className="detail-text">{pr.justification}</p>
          </div>
        )}
      </div>

      {/* Rejection Note */}
      {isRejected && pr.approval_note && (
        <div className="alert alert-error">
          <strong>Alasan Penolakan:</strong> {pr.approval_note}
        </div>
      )}

      {/* Approval Note (non-rejection) */}
      {!isRejected && pr.approval_note && (
        <div className="alert alert-success">
          <strong>Catatan Approval:</strong> {pr.approval_note}
        </div>
      )}

      {/* Line Items */}
      {pr.line_items && pr.line_items.length > 0 && (
        <div className="detail-card">
          <div className="line-items-header">
            <h3>List Items</h3>
            <span className="line-items-count">{pr.line_items.length} item</span>
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>No</th>
                  <th>Nama Item</th>
                  <th>Qty</th>
                  <th>Satuan</th>
                  <th className="text-right">Harga Satuan</th>
                  <th className="text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {pr.line_items.map((item, idx) => (
                  <tr key={item.id}>
                    <td>{idx + 1}</td>
                    <td>{item.item_name}</td>
                    <td>{item.quantity}</td>
                    <td>{item.unit_of_measure}</td>
                    <td className="text-right font-mono">
                      {formatCurrency(item.estimated_unit_price)}
                    </td>
                    <td className="text-right font-mono">
                      {formatCurrency(item.subtotal)}
                    </td>
                  </tr>
                ))}
              </tbody>
             <tfoot>
                <tr>
                  <td colSpan={4} />
                  <td className="text-right">Total</td>
                  <td className="text-right font-mono">
                    {formatCurrency(pr.total_amount)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Vendor Quotes */}
      {pr.vendor_quotes && pr.vendor_quotes.length > 0 && (
        <div className="detail-card">
          <h3>Penawaran Vendor</h3>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>No</th>
                  <th>Nama Vendor</th>
                  <th>Kontak</th>
                  <th className="text-right">Harga Penawaran</th>
                  <th>Tanggal Survei</th>
                  <th>Status</th>
                  <th>Bukti</th>
                </tr>
              </thead>
              <tbody>
                {pr.vendor_quotes.map((quote, idx) => (
                  <tr key={quote.id} style={quote.is_recommended ? { background: "rgba(59, 130, 246, 0.05)" } : {}}>
                    <td>{idx + 1}</td>
                    <td>
                      <strong>{quote.vendor_name}</strong>
                      {quote.is_recommended && (
                        <span style={{ marginLeft: "0.5rem", fontSize: "0.875rem", color: "#2563eb" }}>
                          (Rekomendasi)
                        </span>
                      )}
                    </td>
                    <td>{quote.vendor_contact}</td>
                    <td className="text-right font-mono">
                      {formatCurrency(quote.quoted_price)}
                    </td>
                    <td>{formatDateID(quote.survey_date)}</td>
                    <td>
                      {quote.is_recommended ? (
                        <span style={{ color: "#16a34a", fontWeight: 600 }}>✓ Terpilih</span>
                      ) : (
                        <span className="text-muted">Alternatif</span>
                      )}
                    </td>
                    <td>
                      {quote.survey_evidence_url ? (
                        <a
                          href={`${import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:9395'}/${quote.survey_evidence_url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn btn-sm btn-outline"
                        >
                          Lihat Bukti
                        </a>
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Edit & Cancel Actions (when SUBMITTED, or revise & resubmit when REJECTED) */}
      {(pr.status === "SUBMITTED" || pr.status === "REJECTED") && (
        <div className="action-bar" style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
          <button
            className="btn btn-outline"
            style={{ borderColor: "var(--color-danger, #dc3545)", color: "var(--color-danger, #dc3545)" }}
            onClick={() => setShowDeleteModal(true)}
          >
            Batalkan PR
          </button>
          <Link to={`/requester/pr/${id}/edit`} className="btn btn-primary">
            {pr.status === "REJECTED" ? "Revisi & Ajukan Ulang" : "Edit PR"}
          </Link>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Konfirmasi Pembatalan</h3>
              <button
                className="modal-close"
                onClick={() => setShowDeleteModal(false)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              <p>
                Apakah Anda yakin ingin membatalkan dan menghapus PR{" "}
                <strong>{pr.pr_number}</strong>?
              </p>
              <p className="text-muted" style={{ marginTop: "0.5rem" }}>
                Tindakan ini tidak dapat dibatalkan. PR beserta semua item di dalamnya akan dihapus secara permanen.
              </p>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setShowDeleteModal(false)}
                disabled={deleting}
              >
                Kembali
              </button>
              <button
                type="button"
                className="btn btn-primary"
                style={{ backgroundColor: "var(--color-danger, #dc3545)", borderColor: "var(--color-danger, #dc3545)" }}
                onClick={handleDelete}
                disabled={deleting}
              >
                {deleting ? "Menghapus..." : "Ya, Batalkan PR"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PO Info */}
      {po && (
        <div className="detail-card">
          <h3>Purchase Order</h3>
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">No. PO</span>
              <span className="detail-value font-mono">{po.po_number}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Budget Dialokasikan</span>
              <span className="detail-value font-mono">
                {formatCurrency(po.allocated_budget)}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Tanggal Terbit</span>
              <span className="detail-value">{formatDate(po.issued_at)}</span>
            </div>
          </div>
        </div>
      )}

      {/* GRN Details (when DOC_SUBMITTED, VERIFIED, or CLOSED) */}
      {grn && (["DOC_SUBMITTED", "VERIFIED", "CLOSED"].includes(pr.status)) && (
        <div className="detail-card">
          <h3>Dokumen GRN</h3>
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">Commercial Invoice</span>
              <span className="detail-value">
                <a 
                  href={`${import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:9395'}/${grn.commercial_invoice_url ?? ''}`}
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="btn btn-sm btn-outline"
                >
                  Lihat Dokumen
                </a>
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Foto Barang</span>
              <span className="detail-value">
                <a 
                  href={`${import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:9395'}/${grn.goods_photo_url ?? ''}`}
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="btn btn-sm btn-outline"
                >
                  Lihat Foto
                </a>
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Tanggal Submit</span>
              <span className="detail-value">{formatDate(grn.submitted_at)}</span>
            </div>
          </div>
          {grn.verification_note && (
            <div className="detail-section" style={{ marginTop: "1rem" }}>
              <span className="detail-label">Catatan Verifikasi Admin</span>
              <div className="alert alert-info" style={{ marginTop: "0.5rem" }}>
                {grn.verification_note}
              </div>
            </div>
          )}
        </div>
      )}

      {/* GRN Submit Button (only when PO_ISSUED) */}
      {pr.status === "PO_ISSUED" && po && (
        <>
          {grnReturnNote && (
            <div className="alert alert-error">
              <strong>Dokumen GRN dikembalikan:</strong> {grnReturnNote}
              <br />
              Silakan perbaiki dan upload ulang dokumen di bawah ini.
            </div>
          )}
          <div className="action-bar">
            <button
              className="btn btn-primary"
              onClick={() => setShowGrnModal(true)}
            >
              {grnReturnNote ? "Upload Ulang Dokumen GRN" : "Submit GRN Documents"}
            </button>
          </div>
        </>
      )}

      {/* GRN Upload Modal */}
      {showGrnModal && (
        <div className="modal-overlay" onClick={() => setShowGrnModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Submit Dokumen GRN</h3>
              <button
                className="modal-close"
                onClick={() => setShowGrnModal(false)}
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleGrnSubmit}>
              <div className="modal-body">
                <p className="text-muted" style={{ marginBottom: "1rem" }}>
                  Upload dokumen bukti penerimaan barang. Format: JPG, PNG, atau
                  PDF (maks 5MB per file).
                </p>
                <div className="form-group">
                  <label>Commercial Invoice *</label>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,.pdf"
                    onChange={(e) => setInvoiceFile(e.target.files?.[0] ?? null)}
                  />
                  {invoiceFile && (
                    <span className="text-muted" style={{ fontSize: "0.9375rem" }}>
                      {invoiceFile.name} ({(invoiceFile.size / 1024).toFixed(0)} KB)
                    </span>
                  )}
                </div>
                <div className="form-group">
                  <label>Foto Barang Diterima *</label>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,.pdf"
                    onChange={(e) => setPhotoFile(e.target.files?.[0] ?? null)}
                  />
                  {photoFile && (
                    <span className="text-muted" style={{ fontSize: "0.9375rem" }}>
                      {photoFile.name} ({(photoFile.size / 1024).toFixed(0)} KB)
                    </span>
                  )}
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowGrnModal(false)}
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={uploading || !invoiceFile || !photoFile}
                >
                  {uploading ? "Mengupload..." : "Submit Dokumen"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
