import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useProcurement } from "../../contexts/ProcurementContext";
import StatusBadge from "../../components/StatusBadge";

export default function RequesterDashboard() {
  const { prs, prsLoading, fetchMyPRs } = useProcurement();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMyPRs().catch(() => setError("Gagal memuat data requisition."));
  }, [fetchMyPRs]);

  return (
    <div className="page">
      <div className="page-header">
        <h2>My Purchase Requisitions</h2>
        <Link to="/requester/pr/new" className="btn btn-primary">
          + Buat Requisition
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {prsLoading ? (
        <p className="text-muted">Memuat data...</p>
      ) : prs.length === 0 ? (
        <div className="empty-state">
          <p>Belum ada Purchase Requisition.</p>
          <Link to="/requester/pr/new" className="btn btn-primary">
            Buat Requisition Pertama
          </Link>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>No. PR</th>
                <th>Judul</th>
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
                  <td className="text-right">
                    {new Intl.NumberFormat("id-ID", {
                      style: "currency",
                      currency: "IDR",
                      minimumFractionDigits: 0,
                    }).format(pr.total_amount)}
                  </td>
                  <td>
                    <StatusBadge status={pr.status} />
                  </td>
                  <td>
                    {new Date(pr.created_at).toLocaleDateString("id-ID", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </td>
                  <td>
                    <Link
                      to={`/requester/pr/${pr.id}`}
                      className="btn btn-sm btn-outline"
                    >
                      Detail
                    </Link>
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
