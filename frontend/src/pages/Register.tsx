import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerRequesterRequest } from "../services/auth";

export default function Register() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validasi client-side
    if (!fullName.trim() || !email || !password || !confirmPassword) {
      setError("Semua field wajib diisi.");
      return;
    }

    if (password.length < 8) {
      setError("Password minimal 8 karakter.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Password dan konfirmasi password tidak cocok.");
      return;
    }

    setLoading(true);
    try {
      await registerRequesterRequest(email, password, fullName.trim());
      setSuccess(true);
      // Redirect ke login setelah 2 detik
      setTimeout(() => navigate("/login"), 2000);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Registrasi gagal. Silakan coba lagi.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="login-title">SiCure</h1>
        <p className="login-subtitle">Daftar Akun Requester</p>

        {success ? (
          <div className="alert alert-success">
            Registrasi berhasil! Anda akan dialihkan ke halaman login...
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="login-form">
            {error && <div className="alert alert-error">{error}</div>}

            <div className="form-group">
              <label htmlFor="fullName">Nama Lengkap</label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Masukkan nama lengkap"
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email@example.com"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimal 8 karakter"
                required
                minLength={8}
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Konfirmasi Password</label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Ulangi password"
                required
                minLength={8}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-full"
              disabled={loading}
            >
              {loading ? "Memproses..." : "Daftar"}
            </button>

            <p className="register-link">
              Sudah punya akun? <Link to="/login">Login di sini</Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
