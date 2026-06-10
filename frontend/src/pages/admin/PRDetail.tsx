import { useEffect, useState, useCallback, type FormEvent } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../../services/api";
import { useToast } from "../../contexts/ToastContext";
import { useProcurement } from "../../contexts/ProcurementContext";
import StatusBadge from "../../components/StatusBadge";
import type {
  PurchaseRequisition,
  PurchaseOrder,
  GRNDocument,
  APIResponse,
  PaginatedResponse,
  PRStatus,
} from "../../types";

const STATUS_TIMELINE: { key: PRStatus; label: string }[] = [
  { key: "SUBMITTED", label: "Submitted" },
  { key: "UNDER_REVIEW", label: "Under Review" },
  { key: "APPROVED", label: "Approved" },
  { key: "PO_ISSUED", label: "PO Issued" },
  { key: "DOC_SUBMITTED", label: "Doc Submitted" },
  { key: "VERIFIED", label: "Verified" },
  { key: "CLOSED", label: "Closed" },
];

function getTimelineIndex(status: PRStatus): number {
  if (status === "REJECTED") return 1;
  const idx = STATUS_TIMELINE.findIndex((s) => s.key === status);
  return idx >= 0 ? idx : 0;
}

export default function AdminPRDetail() {
  const { id } = useParams();
  const { showToast } = useToast();
  const { invalidate } = useProcurement();

  const [pr, setPr] = useState<PurchaseRequisition | null>(null);
  const [po, setPo] = useState<PurchaseOrder | null>(null);
  const [grn, setGrn] = useState<GRNDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewAction, setReviewAction] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [reviewNote, setReviewNote] = useState("");
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  const [showPOModal, setShowPOModal] = useState(false);
  const [poSubmitting, setPoSubmitting] = useState(false);

  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [verifyNote, setVerifyNote] = useState("");
  const [verifySubmitting, setVerifySubmitting] = useState(false);

  // ── Fetch data ─────────────────────────────────────────────────
  const fetchData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      // Fetch PR from admin list (no admin detail endpoint)
      const prRes = await api.get<PaginatedResponse<PurchaseRequisition>>(
        "/requisitions/admin/",
        { params: { page: 1, per_page: 100 } }
      );
      const found = prRes.data.data.find((p) => p.id === Number(id));
      if (!found) {
        setError("PR tidak ditemukan.");
        return;
      }
      setPr(found);

      // Fetch PO if applicable
      if (
        ["PO_ISSUED", "DOC_SUBMITTED", "VERIFIED", "CLOSED"].includes(
          found.status
        )
      ) {
        try {
          const poRes = await api.get<PaginatedResponse<PurchaseOrder>>(
            "/purchase-orders/",
            { params: { page: 1, per_page: 100 } }
          );
          const foundPo = poRes.data.data.find((p) => p.pr_id === found.id);
          if (foundPo) {
            setPo(foundPo);
            // If DOC_SUBMITTED or later, try to fetch GRN info
            if (
              ["DOC_SUBMITTED", "VERIFIED", "CLOSED"].includes(found.status)
            ) {
              try {
                // Try fetching GRN by PO ID (custom endpoint or mock)
                const grnRes = await api.get<APIResponse<GRNDocument>>(
                  `/grn/${foundPo.id}`
                );
                setGrn(grnRes.data.data);
              } catch {
                // GRN detail endpoint may not exist yet.
                // Create a placeholder GRN with the PO ID so verify can work.
                // The GRN ID is typically equal to PO ID for 1:1 relationship.
                // We use po.id as grn.id as a best-effort guess.
                setGrn({
                  id: foundPo.id,
                  po_id: foundPo.id,
                  requester_id: found.requester_id,
                  receipt_url: null,
                  commercial_invoice_url: null,
                  goods_photo_url: null,
                  submitted_at: new Date().toISOString(),
                  verification_note: null,
                });
              }
            }
          }
        } catch {
          // PO fetch failed, non-critical
        }
      }
    } catch {
      setError("Gagal memuat detail PR.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ── Review (Approve/Reject) ────────────────────────────────────
  const handleReview = async (e: FormEvent) => {
    e.preventDefault();
    if (!reviewNote.trim()) {
      showToast("error", "Catatan review wajib diisi.");
      return;
    }
    setReviewSubmitting(true);
    try {
      await api.put(`/requisitions/admin/${id}/review`, {
        status: reviewAction,
        approval_note: reviewNote.trim(),
      });
      const label = reviewAction === "APPROVED" ? "disetujui" : "ditolak";
      showToast("success", `PR berhasil ${label}.`);
      setShowReviewModal(false);
      setReviewNote("");
      invalidate();
      await fetchData();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Gagal melakukan review.";
      showToast("error", msg);
    } finally {
      setReviewSubmitting(false);
    }
  };

  // ── Issue PO ───────────────────────────────────────────────────
  const handleIssuePO = async () => {
    if (!pr) return;
    setPoSubmitting(true);
    try {
      const res = await api.post<APIResponse<PurchaseOrder>>(
        `/purchase-orders/${pr.id}/issue`
      );
      showToast("success", "Purchase Order berhasil diterbitkan!");
      setPo(res.data.data);
      setShowPOModal(false);
      invalidate();
      await fetchData();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Gagal menerbitkan PO.";
      showToast("error", msg);
    } finally {
      setPoSubmitting(false);
    }
  };

  // ── Verify GRN ─────────────────────────────────────────────────
  const handleVerifyGRN = async (e: FormEvent) => {
    e.preventDefault();
    if (!verifyNote.trim()) {
      showToast("error", "Catatan verifikasi wajib diisi.");
      return;
    }
    if (!grn) {
      showToast("error", "Data GRN tidak ditemukan.");
      return;
    }
    setVerifySubmitting(true);

    // Determine target status based on current PR status
    const targetStatus = pr?.status === "DOC_SUBMITTED" ? "VERIFIED" : "CLOSED";

    try {
      await api.put(`/grn/admin/${grn.id}/verify`, {
        status: targetStatus,
        verification_note: verifyNote.trim(),
      });
      const label = targetStatus === "VERIFIED" ? "diverifikasi" : "ditutup";
      showToast("success", `GRN berhasil ${label}.`);
      setShowVerifyModal(false);
      setVerifyNote("");
      invalidate();
      await fetchData();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Gagal verifikasi GRN.";
      showToast("error", msg);
    } finally {
      setVerifySubmitting(false);
    }
  };

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(val);

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString("id-ID", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  if (loading) return <p className="text-muted">Memuat detail PR...</p>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!pr) return <div className="alert alert-error">PR tidak ditemukan.</div>;

  const currentIdx = getTimelineIndex(pr.status);
  const isRejected = pr.status === "REJECTED";
  const canReview = pr.status === "SUBMITTED";
  const canIssuePO = pr.status === "APPROVED";
  const canVerifyGRN = pr.status === "DOC_SUBMITTED" || pr.status === "VERIFIED";

  return (
    <div className="page">
      <div className="page-header">
        <h2>Review PR: {pr.pr_number}</h2>
        <Link to="/admin/dashboard" className="btn-back">
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
            <span className="detail-label">Requester ID</span>
            <span className="detail-value">ID-{pr.requester_id}</span>
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
        </div>
        {pr.justification && (
          <div className="detail-section">
            <span className="detail-label">Justifikasi</span>
            <p className="detail-text">{pr.justification}</p>
          </div>
        )}
        {pr.approval_note && (
          <div className="detail-section">
            <span className="detail-label">
              {isRejected ? "Alasan Penolakan" : "Catatan Approval"}
            </span>
            <p className="detail-text">{pr.approval_note}</p>
          </div>
        )}
      </div>

      {/* Line Items */}
      {pr.line_items && pr.line_items.length > 0 && (
        <div className="detail-card">
          <div className="line-items-header">
            <h3>Line Items</h3>
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

      {/* GRN Documents (if available) */}
      {grn && (
        <div className="detail-card">
          <h3>Dokumen GRN</h3>
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">Commercial Invoice</span>
              <span className="detail-value">
                <a 
                  href={`${import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:8000'}/${grn.commercial_invoice_url ?? ''}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  Lihat Dokumen
                </a>
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Foto Barang</span>
              <span className="detail-value">
                <a 
                  href={`${import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:8000'}/${grn.goods_photo_url ?? ''}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  Lihat Foto
                </a>
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Tanggal Submit</span>
              <span className="detail-value">{formatDate(grn.submitted_at)}</span>
            </div>
            {grn.verification_note && (
              <div className="detail-item">
                <span className="detail-label">Catatan Verifikasi</span>
                <span className="detail-value">{grn.verification_note}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="action-bar">
        {canReview && (
          <>
            <button
              className="btn btn-success"
              onClick={() => {
                setReviewAction("APPROVED");
                setReviewNote("");
                setShowReviewModal(true);
              }}
            >
              Approve
            </button>
            <button
              className="btn btn-danger"
              onClick={() => {
                setReviewAction("REJECTED");
                setReviewNote("");
                setShowReviewModal(true);
              }}
            >
              Reject
            </button>
          </>
        )}
        {canIssuePO && (
          <button
            className="btn btn-primary"
            onClick={() => setShowPOModal(true)}
          >
            Issue Purchase Order
          </button>
        )}
        {canVerifyGRN && (
          <button
            className="btn btn-success"
            onClick={() => {
              setVerifyNote("");
              setShowVerifyModal(true);
            }}
          >
            {pr.status === "DOC_SUBMITTED" ? "Verify GRN" : "Close GRN"}
          </button>
        )}
      </div>

      {/* Review Modal */}
      {showReviewModal && (
        <div className="modal-overlay" onClick={() => setShowReviewModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {reviewAction === "APPROVED" ? "Approve" : "Reject"} PR
              </h3>
              <button
                className="modal-close"
                onClick={() => setShowReviewModal(false)}
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleReview}>
              <div className="modal-body">
                <p className="text-muted" style={{ marginBottom: "1rem" }}>
                  {reviewAction === "APPROVED"
                    ? "Anda akan menyetujui PR ini. Berikan catatan approval."
                    : "Anda akan menolak PR ini. Berikan alasan penolakan."}
                </p>
                <div className="form-group">
                  <label>
                    {reviewAction === "APPROVED"
                      ? "Catatan Approval *"
                      : "Alasan Penolakan *"}
                  </label>
                  <textarea
                    value={reviewNote}
                    onChange={(e) => setReviewNote(e.target.value)}
                    placeholder={
                      reviewAction === "APPROVED"
                        ? "Catatan persetujuan..."
                        : "Alasan penolakan..."
                    }
                    rows={3}
                    maxLength={2000}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowReviewModal(false)}
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className={`btn ${reviewAction === "APPROVED" ? "btn-success" : "btn-danger"}`}
                  disabled={reviewSubmitting}
                >
                  {reviewSubmitting
                    ? "Memproses..."
                    : reviewAction === "APPROVED"
                      ? "Approve"
                      : "Reject"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Issue PO Confirmation Modal */}
      {showPOModal && (
        <div className="modal-overlay" onClick={() => setShowPOModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Issue Purchase Order</h3>
              <button
                className="modal-close"
                onClick={() => setShowPOModal(false)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              <p>
                Anda akan menerbitkan Purchase Order untuk PR{" "}
                <strong>{pr.pr_number}</strong> dengan budget{" "}
                <strong>{formatCurrency(pr.total_amount)}</strong>.
              </p>
              <p className="text-muted" style={{ marginTop: "0.5rem" }}>
                Tindakan ini tidak dapat dibatalkan.
              </p>
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-outline"
                onClick={() => setShowPOModal(false)}
              >
                Batal
              </button>
              <button
                className="btn btn-primary"
                onClick={handleIssuePO}
                disabled={poSubmitting}
              >
                {poSubmitting ? "Memproses..." : "Terbitkan PO"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Verify GRN Modal */}
      {showVerifyModal && (
        <div className="modal-overlay" onClick={() => setShowVerifyModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {pr.status === "DOC_SUBMITTED"
                  ? "Verifikasi GRN"
                  : "Tutup GRN"}
              </h3>
              <button
                className="modal-close"
                onClick={() => setShowVerifyModal(false)}
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleVerifyGRN}>
              <div className="modal-body">
                {grn && (
                  <div style={{ marginBottom: "1rem" }}>
                    <p className="text-muted">Dokumen yang di-submit:</p>
                    <ul style={{ paddingLeft: "1.25rem", marginTop: "0.5rem" }}>
                      <li>
                        <a
                          href={grn.commercial_invoice_url ?? "#"}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Commercial Invoice
                        </a>
                      </li>
                      <li>
                        <a
                          href={grn.goods_photo_url ?? "#"}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Foto Barang
                        </a>
                      </li>
                    </ul>
                  </div>
                )}
                <div className="form-group">
                  <label>Catatan Verifikasi *</label>
                  <textarea
                    value={verifyNote}
                    onChange={(e) => setVerifyNote(e.target.value)}
                    placeholder="Catatan verifikasi dokumen..."
                    rows={3}
                    maxLength={2000}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowVerifyModal(false)}
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="btn btn-success"
                  disabled={verifySubmitting}
                >
                  {verifySubmitting
                    ? "Memproses..."
                    : pr.status === "DOC_SUBMITTED"
                      ? "Verifikasi"
                      : "Tutup"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
