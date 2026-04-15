import { Outlet, Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isAdmin = user?.role === "admin";
  const dashboardPath = isAdmin ? "/admin/dashboard" : "/requester/dashboard";

  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="navbar-left">
          <Link to={dashboardPath} className="navbar-brand">
            SiCure
          </Link>
          <span className="navbar-divider">|</span>
          <Link
            to={dashboardPath}
            className={
              location.pathname === dashboardPath ? "nav-link active" : "nav-link"
            }
          >
            Dashboard
          </Link>
        </div>
        <div className="navbar-right">
          <span className="role-badge" data-role={user?.role}>
            {isAdmin ? "Admin" : "Requester"}
          </span>
          <span className="user-name">{user?.full_name}</span>
          <button className="btn btn-logout" onClick={logout}>
            Logout
          </button>
        </div>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
