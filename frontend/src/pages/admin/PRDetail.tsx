import { useParams, Link } from "react-router-dom";

export default function AdminPRDetail() {
  const { id } = useParams();

  return (
    <div className="page">
      <div className="page-header">
        <h2>Review Purchase Requisition #{id}</h2>
        <Link to="/admin/dashboard" className="btn btn-outline">
          &larr; Kembali
        </Link>
      </div>
      <div className="placeholder-card">
        <p>
          Halaman review PR (approve/reject, issue PO, verify GRN) akan
          diimplementasi selanjutnya.
        </p>
      </div>
    </div>
  );
}
