import api from "./api";
import type { TokenResponse, User } from "../types";

export async function loginRequest(
  email: string,
  password: string
): Promise<{ token: string; user: User }> {
  const tokenRes = await api.post<TokenResponse>("/auth/login", {
    email,
    password,
  });
  const { access_token, refresh_token } = tokenRes.data;

  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);

  const userRes = await api.get<User>("/auth/me");
  const user = userRes.data;

  return { token: access_token, user };
}

export async function refreshTokenRequest(): Promise<string> {
  const refresh_token = localStorage.getItem("refresh_token");
  if (!refresh_token) {
    throw new Error("No refresh token available");
  }

  const res = await api.post<TokenResponse>("/auth/refresh", {
    refresh_token,
  });
  const { access_token, refresh_token: new_refresh } = res.data;

  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", new_refresh);

  return access_token;
}

export async function logoutRequest(): Promise<void> {
  try {
    await api.post("/auth/logout");
  } catch {
    // Ignore errors — we clear local storage regardless
  } finally {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
  }
}

export async function registerRequesterRequest(
  email: string,
  password: string,
  full_name: string
): Promise<User> {
  const res = await api.post<User>("/auth/register-requester", {
    email,
    password,
    full_name,
  });
  return res.data;
}
