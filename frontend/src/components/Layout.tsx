import { Outlet, Link, useLocation } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "../contexts/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const isAdmin = user?.role === "admin";
  const dashboardPath = isAdmin ? "/admin/dashboard" : "/requester/dashboard";

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    }
    if (showUserMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showUserMenu]);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
    setShowUserMenu(false);
  }, [location.pathname]);

  const navLinks = [
    { to: dashboardPath, label: "Dashboard", show: true },
    { to: "/requester/pr/new", label: "Buat PR", show: !isAdmin },
  ].filter((l) => l.show);

  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="navbar-inner">
          {/* Brand */}
          <Link to={dashboardPath} className="navbar-brand">
            <span className="brand-logo">S</span>
            <span className="brand-text">SiCure</span>
          </Link>

          {/* Desktop Nav Links */}
          <div className="navbar-nav">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`nav-link${location.pathname === link.to ? " nav-link-active" : ""}`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right Section */}
          <div className="navbar-actions">
            {/* Role Badge */}
            <span className={`nav-role-badge${isAdmin ? " nav-role-admin" : ""}`}>
              {isAdmin ? "Admin" : "Requester"}
            </span>

            {/* User Dropdown */}
            <div className="nav-user" ref={dropdownRef}>
              <button
                className="nav-user-btn"
                onClick={() => setShowUserMenu((v) => !v)}
                aria-expanded={showUserMenu}
                aria-label="User menu"
              >
                <span className="nav-avatar">
                  {user?.full_name?.charAt(0).toUpperCase() || "U"}
                </span>
                <span className="nav-user-name">{user?.full_name}</span>
                <svg
                  className={`nav-chevron${showUserMenu ? " nav-chevron-open" : ""}`}
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {showUserMenu && (
                <div className="nav-dropdown">
                  <div className="nav-dropdown-header">
                    <span className="nav-dropdown-name">{user?.full_name}</span>
                    <span className="nav-dropdown-email">{user?.email}</span>
                  </div>
                  <div className="nav-dropdown-divider" />
                  <button className="nav-dropdown-item nav-dropdown-logout" onClick={logout}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                      <polyline points="16 17 21 12 16 7" />
                      <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                    Logout
                  </button>
                </div>
              )}
            </div>

            {/* Mobile Hamburger */}
            <button
              className={`nav-hamburger${mobileMenuOpen ? " nav-hamburger-active" : ""}`}
              onClick={() => setMobileMenuOpen((v) => !v)}
              aria-label="Toggle menu"
            >
              <span />
              <span />
              <span />
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="nav-mobile-menu">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`nav-mobile-link${location.pathname === link.to ? " nav-mobile-link-active" : ""}`}
              >
                {link.label}
              </Link>
            ))}
            <div className="nav-mobile-divider" />
            <div className="nav-mobile-user">
              <span className="nav-avatar">
                {user?.full_name?.charAt(0).toUpperCase() || "U"}
              </span>
              <div className="nav-mobile-user-info">
                <span className="nav-mobile-user-name">{user?.full_name}</span>
                <span className="nav-mobile-user-email">{user?.email}</span>
              </div>
            </div>
            <button className="nav-mobile-logout" onClick={logout}>
              Logout
            </button>
          </div>
        )}
      </nav>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
