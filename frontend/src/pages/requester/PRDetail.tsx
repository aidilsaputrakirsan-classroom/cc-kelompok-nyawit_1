import { useParams, Link } from "react-router-dom";

export default function RequesterPRDetail() {
  const { id } = useParams();

  return (
    <div className="page">
      <div className="page-header">
        <h2>Detail Purchase Requisition #{id}</h2>
        <Link to="/requester/dashboard" className="btn btn-outline">
          &larr; Kembali
        </Link>
      </div>
      <div className="placeholder-card">
        <p>Halaman detail PR akan diimplementasi selanjutnya.</p>
      </div>
    </div>
  );
}
