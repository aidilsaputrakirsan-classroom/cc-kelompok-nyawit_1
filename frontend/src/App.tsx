import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ToastProvider } from "./contexts/ToastContext";
import { ProcurementProvider } from "./contexts/ProcurementContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import RequesterDashboard from "./pages/requester/Dashboard";
import RequesterPRNew from "./pages/requester/PRNew";
import RequesterPRDetail from "./pages/requester/PRDetail";
import AdminDashboard from "./pages/admin/Dashboard";
import AdminPRDetail from "./pages/admin/PRDetail";
import AdminPODetail from "./pages/admin/PODetail";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <ProcurementProvider>
            <Routes>
              {/* Public */}
              <Route path="/login" element={<Login />} />

              {/* Requester routes */}
              <Route
                element={
                  <ProtectedRoute allowedRoles={["requester"]}>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route path="/requester/dashboard" element={<RequesterDashboard />} />
                <Route path="/requester/pr/new" element={<RequesterPRNew />} />
                <Route path="/requester/pr/:id" element={<RequesterPRDetail />} />
              </Route>

              {/* Admin routes */}
              <Route
                element={
                  <ProtectedRoute allowedRoles={["admin"]}>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route path="/admin/dashboard" element={<AdminDashboard />} />
                <Route path="/admin/pr/:id" element={<AdminPRDetail />} />
                <Route path="/admin/po/:id" element={<AdminPODetail />} />
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
