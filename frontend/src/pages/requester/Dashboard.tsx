import { useEffect, useState, type ChangeEvent } from "react";
import { Link } from "react-router-dom";
import { useProcurement } from "../../contexts/ProcurementContext";
import StatusBadge from "../../components/StatusBadge";
import StatsCard from "../../components/StatsCard";
import { useDebounce, useKeyboardShortcut } from "../../hooks";

export default function RequesterDashboard() {
  const { prs, prsLoading, fetchMyPRs } = useProcurement();
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const debouncedSearch = useDebounce(searchQuery, 300);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const itemsPerPage = 10;

  useEffect(() => {
    fetchMyPRs().catch(() => setError("Gagal memuat data requisition."));
  }, [fetchMyPRs]);

  // Calculate stats
  const stats = {
    total: prs.length,
    inProgress: prs.filter((pr) => 
      ["SUBMITTED", "UNDER_REVIEW", "APPROVED"].includes(pr.status)
    ).length,
    poIssued: prs.filter((pr) => pr.status === "PO_ISSUED").length,
    completed: prs.filter((pr) => 
      ["VERIFIED", "CLOSED"].includes(pr.status)
    ).length,
  };

  // Filter and search PRs (debounced)
  const filteredPRs = prs.filter((pr) => {
    return !debouncedSearch || 
      pr.pr_number.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
      pr.title.toLowerCase().includes(debouncedSearch.toLowerCase());
  });

  // Pagination
  const totalPages = Math.ceil(filteredPRs.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedPRs = filteredPRs.slice(startIndex, endIndex);

  // Reset to page 1 when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearch]);

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
    },
    enabled: searchQuery !== "",
    preventDefault: false,
  });



  return (
    <div className="page">
      <div className="page-header">
        <h2>My Purchase Requisitions</h2>
        <div style={{ display: "flex", gap: "var(--spacing-md)", alignItems: "center" }}>
          <Link to="/requester/pr/new" className="btn btn-primary">
            + Buat Requisition
          </Link>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Search Bar */}
      {!prsLoading && prs.length > 0 && (
        <div className="search-bar">
          <input
            type="text"
            placeholder="🔍 Cari berdasarkan No. PR atau judul..."
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
      {!prsLoading && prs.length > 0 && (
        <div className="stats-grid">
          <StatsCard
            label="Total PR"
            value={stats.total}
            icon="📋"
          />
          <StatsCard
            label="In Progress"
            value={stats.inProgress}
            icon="⏳"
          />
          <StatsCard
            label="PO Issued"
            value={stats.poIssued}
            icon="📄"
          />
          <StatsCard
            label="Completed"
            value={stats.completed}
            icon="✨"
          />
        </div>
      )}

      {prsLoading ? (
        <div className="skeleton-loader">
          <div className="skeleton skeleton-card" style={{ height: "400px" }}></div>
        </div>
      ) : filteredPRs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <h3>{searchQuery ? "Tidak Ada Hasil Pencarian" : "Belum Ada Data"}</h3>
          <p>
            {searchQuery
              ? "Tidak ada Purchase Requisition yang sesuai dengan pencarian Anda."
              : "Anda belum membuat Purchase Requisition apapun."}
          </p>
          {searchQuery ? (
            <button 
              className="btn btn-outline" 
              onClick={() => setSearchQuery("")}
            >
              Clear Search
            </button>
          ) : (
            <Link to="/requester/pr/new" className="btn btn-primary">
              Buat Requisition Pertama
            </Link>
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
                  <th>No. PR</th>
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
