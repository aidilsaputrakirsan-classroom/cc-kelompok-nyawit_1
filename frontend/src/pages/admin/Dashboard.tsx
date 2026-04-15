import { useEffect, useState, type ChangeEvent } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";
import StatusBadge from "../../components/StatusBadge";
import type {
  PurchaseRequisition,
  PaginatedResponse,
  PRStatus,
} from "../../types";

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Semua Status" },
  { value: "SUBMITTED", label: "Submitted" },
  { value: "UNDER_REVIEW", label: "Under Review" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
  { value: "PO_ISSUED", label: "PO Issued" },
  { value: "DOC_SUBMITTED", label: "Doc Pending" },
  { value: "VERIFIED", label: "Verified" },
  { value: "CLOSED", label: "Closed" },
];

/** Determine which action buttons to show based on PR status */
function getActions(pr: PurchaseRequisition) {
  const actions: { label: string; to: string; variant: string }[] = [];

  if (pr.status === "SUBMITTED" || pr.status === "UNDER_REVIEW") {
    actions.push({
      label: "Review",
      to: `/admin/pr/${pr.id}`,
      variant: "btn-warning",
    });
  }
  if (pr.status === "APPROVED") {
    actions.push({
      label: "Issue PO",
      to: `/admin/pr/${pr.id}`,
      variant: "btn-primary",
    });
  }
  if (pr.status === "DOC_SUBMITTED") {
    actions.push({
      label: "Verify GRN",
      to: `/admin/pr/${pr.id}`,
      variant: "btn-success",
    });
  }

  // Always allow viewing detail
  if (actions.length === 0) {
    actions.push({
      label: "Detail",
      to: `/admin/pr/${pr.id}`,
      variant: "btn-outline",
    });
  }

  return actions;
}

export default function AdminDashboard() {
  const [prs, setPrs] = useState<PurchaseRequisition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const fetchData = (status?: string) => {
    setLoading(true);
    setError(null);
    const params: Record<string, string | number> = { page: 1, per_page: 50 };
    if (status) params.status = status;

    api
      .get<PaginatedResponse<PurchaseRequisition>>(
        "/requisitions/admin/",
        { params }
      )
      .then((res) => setPrs(res.data.data))
      .catch(() => setError("Gagal memuat data requisition."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData(statusFilter);
  }, [statusFilter]);

  const handleFilterChange = (e: ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>Semua Purchase Requisitions</h2>
        <div className="filter-group">
          <label htmlFor="status-filter">Filter:</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={handleFilterChange}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <p className="text-muted">Memuat data...</p>
      ) : prs.length === 0 ? (
        <div className="empty-state">
          <p>Tidak ada Purchase Requisition{statusFilter ? " dengan status ini" : ""}.</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>No. PR</th>
                <th>Judul</th>
                <th>Requester</th>
                <th>Total</th>
                <th>Status</th>
                <th>Tanggal</th>
                <th>Aksi</th>
              </tr>
            </thead>
            <tbody>
              {prs.map((pr) => (
                <tr key={pr.id}>
                  <td className="font-mono">{pr.pr_number}</td>
                  <td>{pr.title}</td>
                  <td>ID-{pr.requester_id}</td>
                  <td className="text-right">
                    {new Intl.NumberFormat("id-ID", {
                      style: "currency",
                      currency: "IDR",
                      minimumFractionDigits: 0,
                    }).format(pr.total_amount)}
                  </td>
                  <td>
                    <StatusBadge status={pr.status as PRStatus} />
                  </td>
                  <td>
                    {new Date(pr.created_at).toLocaleDateString("id-ID", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </td>
                  <td className="actions-cell">
                    {getActions(pr).map((action) => (
                      <Link
                        key={action.label}
                        to={action.to}
                        className={`btn btn-sm ${action.variant}`}
                      >
                        {action.label}
                      </Link>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
