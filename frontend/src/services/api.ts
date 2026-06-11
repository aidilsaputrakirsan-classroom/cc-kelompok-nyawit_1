import axios from "axios";
import { API_BASE_URL } from "../config/gateway";
import {
  getFriendlyApiErrorMessage,
  isServiceUnavailable,
  SERVICE_UNAVAILABLE_MESSAGE,
} from "../utils/apiError";
import { notifyApiError } from "../utils/apiErrorEvents";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach JWT token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Auto-refresh on 401 ──────────────────────────────────────────
let isRefreshing = false;
let pendingRequests: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processPendingRequests(token: string | null, error: unknown = null) {
  pendingRequests.forEach(({ resolve, reject }) => {
    if (token) {
      resolve(token);
    } else {
      reject(error);
    }
  });
  pendingRequests = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const isAuthEndpoint =
      originalRequest?.url?.includes("/auth/login") ||
      originalRequest?.url?.includes("/auth/refresh") ||
      originalRequest?.url?.includes("/auth/register");

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          pendingRequests.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const res = await api.post("/auth/refresh", { refresh_token: refreshToken });
        const { access_token, refresh_token: newRefresh } = res.data.data;

        localStorage.setItem("access_token", access_token);
        localStorage.setItem("refresh_token", newRefresh);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        processPendingRequests(access_token);
        return api(originalRequest);
      } catch (refreshError) {
        processPendingRequests(null, refreshError);
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    const status = error.response?.status;
    const shouldNotifyGlobally =
      !originalRequest?.skipGlobalErrorHandler &&
      (isServiceUnavailable(status) || status === 429 || (status !== undefined && status >= 500));

    if (shouldNotifyGlobally) {
      const message = isServiceUnavailable(status)
        ? SERVICE_UNAVAILABLE_MESSAGE
        : getFriendlyApiErrorMessage(error);
      notifyApiError(message);
    }

    return Promise.reject(error);
  }
);

export default api;
