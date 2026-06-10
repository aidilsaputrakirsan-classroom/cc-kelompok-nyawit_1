import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react";
import { AuthProvider } from "./contexts/AuthContext";
import { ToastProvider } from "./contexts/ToastContext";
import { ProcurementProvider } from "./contexts/ProcurementContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

// Lazy load pages for code splitting
const Login = lazy(() => import("./pages/Login"));
const RequesterDashboard = lazy(() => import("./pages/requester/Dashboard"));
const RequesterPRNew = lazy(() => import("./pages/requester/PRNew"));
const RequesterPRDetail = lazy(() => import("./pages/requester/PRDetail"));
const AdminDashboard = lazy(() => import("./pages/admin/Dashboard"));
const AdminPRDetail = lazy(() => import("./pages/admin/PRDetail"));
const AdminPODetail = lazy(() => import("./pages/admin/PODetail"));

// Loading fallback component
const PageLoader = () => (
  <div className="loading-screen">
    <div className="spinner"></div>
  </div>
);

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <ProcurementProvider>
            <Routes>
              {/* Public */}
              <Route
                path="/login"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Login />
                  </Suspense>
                }
              />

              {/* Requester routes */}
              <Route
                element={
                  <ProtectedRoute allowedRoles={["requester"]}>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route
                  path="/requester/dashboard"
                  element={
                    <Suspense fallback={<PageLoader />}>
                      <RequesterDashboard />
                    </Suspense>
                  }
                />
                <Route
                  path="/requester/pr/new"
                  element={
                    <Suspense fallback={<PageLoader />}>
                      <RequesterPRNew />
                    </Suspense>
                  }
                />
                <Route
                  path="/requester/pr/:id"
                  element={
                    <Suspense fallback={<PageLoader />}>
                      <RequesterPRDetail />
                    </Suspense>
                  }
                />
              </Route>

              {/* Admin routes */}
              <Route
                element={
                  <ProtectedRoute allowedRoles={["admin"]}>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route
                  path="/admin/dashboard"
                  element={
                    <Suspense fallback={<PageLoader />}>
                      <AdminDashboard />
                    </Suspense>
                  }
                />
                <Route
                  path="/admin/pr/:id"
                  element={
                    <Suspense fallback={<PageLoader />}>
                      <AdminPRDetail />
                    </Suspense>
                  }
                />
                <Route
                  path="/admin/po/:id"
                  element={
                    <Suspense fallback={<PageLoader />}>
                      <AdminPODetail />
                    </Suspense>
                  }
                />
              </Route>

              {/* Catch-all */}
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </ProcurementProvider>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
