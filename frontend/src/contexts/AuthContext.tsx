import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { loginRequest } from "../services/auth";
import api from "../services/api";
import type { User, UserRole, APIResponse } from "../types";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (role: UserRole) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Restore session on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      api
        .get<User | APIResponse<User>>("/auth/me")
        .then((res) => {
          const currentUser = "data" in res.data ? res.data.data : res.data;
          setUser(currentUser);
        })
        .catch(() => {
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      setError(null);
      setLoading(true);
      try {
        const { user: loggedInUser } = await loginRequest(email, password);
        localStorage.setItem("user", JSON.stringify(loggedInUser));
        setUser(loggedInUser);

        // Redirect based on role
        const from =
          (location.state as { from?: string })?.from ?? null;
        if (from) {
          navigate(from, { replace: true });
        } else if (loggedInUser.role === "admin") {
          navigate("/admin/dashboard", { replace: true });
        } else {
          navigate("/requester/dashboard", { replace: true });
        }
      } catch (err: unknown) {
        const msg =
          (err as { response?: { data?: { message?: string; detail?: string } } })
            ?.response?.data?.message ??
          (err as { response?: { data?: { message?: string; detail?: string } } })
            ?.response?.data?.detail ??
          "Login gagal. Periksa email dan password.";
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [navigate, location.state]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setUser(null);
    navigate("/login", { replace: true });
  }, [navigate]);

  const hasRole = useCallback(
    (role: UserRole) => {
      return user?.role === role;
    },
    [user]
  );

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
