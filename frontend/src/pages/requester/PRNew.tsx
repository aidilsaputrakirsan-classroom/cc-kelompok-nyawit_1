import { Link } from "react-router-dom";

export default function RequesterPRNew() {
  return (
    <div className="page">
      <div className="page-header">
        <h2>Buat Purchase Requisition Baru</h2>
        <Link to="/requester/dashboard" className="btn btn-outline">
          &larr; Kembali
        </Link>
      </div>
      <div className="placeholder-card">
        <p>Form pembuatan PR akan diimplementasi selanjutnya.</p>
      </div>
    </div>
  );
}
