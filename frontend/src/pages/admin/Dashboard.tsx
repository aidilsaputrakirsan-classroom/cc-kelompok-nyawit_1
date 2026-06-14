import { useEffect, useState, type ChangeEvent } from "react";
import { Link } from "react-router-dom";
import { useProcurement } from "../../contexts/ProcurementContext";
import StatusBadge from "../../components/StatusBadge";
import StatsCard from "../../components/StatsCard";
import { useDebounce, useKeyboardShortcut } from "../../hooks";
import type { PurchaseRequisition, PRStatus } from "../../types";

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Semua Status" },
  { value: "SUBMITTED", label: "Submitted" },
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

  if (pr.status === "SUBMITTED") {
    actions.push({
      label: "Review",
      to: `/admin/pr/${pr.id}`,
      variant: "btn-primary",
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
      variant: "btn-primary",
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
  const { adminPrs, adminPrsLoading, fetchAdminPRs } = useProcurement();
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const debouncedSearch = useDebounce(searchQuery, 300);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const itemsPerPage = 10;

  useEffect(() => {
    fetchAdminPRs(statusFilter).catch(() =>
      setError("Gagal memuat data requisition.")
    );
  }, [statusFilter, fetchAdminPRs]);

  const handleFilterChange = (e: ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
  };

  // Calculate stats
  const stats = {
    total: adminPrs.length,
    pending: adminPrs.filter((pr) => pr.status === "SUBMITTED").length,
    approved: adminPrs.filter((pr) => pr.status === "APPROVED").length,
    completed: adminPrs.filter((pr) => 
      ["VERIFIED", "CLOSED"].includes(pr.status)
    ).length,
  };

  // Filter and search PRs (debounced)
  const filteredPRs = adminPrs.filter((pr) => {
    const matchesStatus = !statusFilter || pr.status === statusFilter;
    const matchesSearch = !debouncedSearch || 
      pr.pr_number.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
      pr.title.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
      `ID-${pr.requester_id}`.toLowerCase().includes(debouncedSearch.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  // Pagination
  const totalPages = Math.ceil(filteredPRs.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedPRs = filteredPRs.slice(startIndex, endIndex);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, debouncedSearch]);

  const handleSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  // Keyboard shortcuts
  useKeyboardShortcut({
    combination: { key: "/", ctrl: false },
    handler: () => {
      const searchInput = document.querySelector(
        '.search-input'
      ) as HTMLInputElement;
      if (searchInput) {
        searchInput.focus();
      }
    },
    enabled: true,
    preventDefault: true,
  });

  useKeyboardShortcut({
    combination: { key: "Escape", ctrl: false },
    handler: () => {
      setSearchQuery("");
      setStatusFilter("");
    },
    enabled: searchQuery !== "" || statusFilter !== "",
    preventDefault: false,
  });



  return (
    <div className="page">
      <div className="page-header">
        <h2>Semua Purchase Requisitions</h2>
        <div style={{ display: "flex", gap: "var(--spacing-md)", alignItems: "center" }}>
          <div className="filter-group" style={{ marginBottom: 0 }}>
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
      </div>

      {/* Search Bar */}
      {!adminPrsLoading && (
        <div className="search-bar">
          <input
            type="text"
            placeholder="🔍 Cari berdasarkan No. PR, judul, atau requester..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="search-input"
          />
          {searchQuery && (
            <button 
              className="btn btn-sm btn-outline" 
              onClick={() => setSearchQuery("")}
              style={{ marginLeft: "var(--spacing-sm)" }}
            >
              Clear
            </button>
          )}

        </div>
      )}

      {/* Stats Cards */}
      {!adminPrsLoading && (
        <div className="stats-grid">
          <StatsCard
            label="Total PR"
            value={stats.total}
            icon="📋"
          />
          <StatsCard
            label="Pending Review"
            value={stats.pending}
            icon="⏳"
          />
          <StatsCard
            label="Approved"
            value={stats.approved}
            icon="✓"
          />
          <StatsCard
            label="Completed"
            value={stats.completed}
            variant="default"
            icon="✨"
          />
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      {adminPrsLoading ? (
        <div className="skeleton-loader">
          <div className="skeleton skeleton-card" style={{ height: "400px" }}></div>
        </div>
      ) : filteredPRs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <h3>Tidak Ada Data</h3>
          <p>
            {searchQuery || statusFilter
              ? "Tidak ada Purchase Requisition yang sesuai dengan filter."
              : "Belum ada Purchase Requisition."}
          </p>
          {(searchQuery || statusFilter) && (
            <button 
              className="btn btn-outline" 
              onClick={() => {
                setSearchQuery("");
                setStatusFilter("");
              }}
            >
              Reset Filter
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="table-info">
            Menampilkan {startIndex + 1}-{Math.min(endIndex, filteredPRs.length)} dari {filteredPRs.length} data
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th style={{ minWidth: "180px" }}>No. PR</th>
                  <th>Requester</th>
                  <th>Judul</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Tanggal</th>
                  <th>Aksi</th>
                </tr>
              </thead>
              <tbody>
                {paginatedPRs.map((pr) => (
                  <tr key={pr.id}>
                    <td className="font-mono" style={{ whiteSpace: "nowrap" }}>{pr.pr_number}</td>
                    <td>{pr.requester_name || `ID-${pr.requester_id}`}</td>
                    <td>{pr.title}</td>
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

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-sm btn-outline"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                ← Previous
              </button>
              <div className="pagination-info">
                Halaman {currentPage} dari {totalPages}
              </div>
              <button
                className="btn btn-sm btn-outline"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
