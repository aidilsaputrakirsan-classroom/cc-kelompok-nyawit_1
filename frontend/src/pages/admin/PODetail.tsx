import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../../services/api";
import StatusBadge from "../../components/StatusBadge";
import type {
  PurchaseOrder,
  PurchaseRequisition,
  APIResponse,
} from "../../types";

export default function AdminPODetail() {
  const { id } = useParams();

  const [po, setPo] = useState<PurchaseOrder | null>(null);
  const [pr, setPr] = useState<PurchaseRequisition | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const poRes = await api.get<APIResponse<PurchaseOrder>>(
        `/purchase-orders/${id}`
      );
      const found = poRes.data.data;
      setPo(found);

      // Fetch the linked PR
      try {
        const prRes = await api.get<APIResponse<PurchaseRequisition>>(
          `/requisitions/admin/${found.pr_id}`
        );
        setPr(prRes.data.data);
      } catch {
        // Non-critical
      }
    } catch {
      setError("Gagal memuat detail PO.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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

  if (loading) return <p className="text-muted">Memuat detail PO...</p>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!po) return <div className="alert alert-error">PO tidak ditemukan.</div>;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Detail PO: {po.po_number}</h2>
        <Link to="/admin/dashboard" className="btn btn-outline">
          &larr; Kembali
        </Link>
      </div>

      <div className="detail-card">
        <h3>Informasi Purchase Order</h3>
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
          <div className="detail-item">
            <span className="detail-label">Issued By (Admin ID)</span>
            <span className="detail-value">ID-{po.issued_by}</span>
          </div>
        </div>
      </div>

      {/* Linked PR */}
      {pr && (
        <div className="detail-card">
          <h3>Purchase Requisition Terkait</h3>
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
          </div>
          <div style={{ marginTop: "1rem" }}>
            <Link to={`/admin/pr/${pr.id}`} className="btn btn-sm btn-outline">
              Lihat Detail PR
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
