import { useParams, Link } from "react-router-dom";

export default function AdminPODetail() {
  const { id } = useParams();

  return (
    <div className="page">
      <div className="page-header">
        <h2>Detail Purchase Order #{id}</h2>
        <Link to="/admin/dashboard" className="btn btn-outline">
          &larr; Kembali
        </Link>
      </div>
      <div className="placeholder-card">
        <p>Halaman detail PO akan diimplementasi selanjutnya.</p>
      </div>
    </div>
  );
}
