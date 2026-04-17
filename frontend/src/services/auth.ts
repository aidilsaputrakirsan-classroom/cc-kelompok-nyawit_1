import api from "./api";
import type { TokenResponse, User, APIResponse } from "../types";

export async function loginRequest(
  email: string,
  password: string
): Promise<{ token: string; user: User }> {
  // Login endpoint returns access_token + refresh_token
  const tokenRes = await api.post<APIResponse<TokenResponse>>("/auth/login", {
    email,
    password,
  });
  const { access_token, refresh_token } = tokenRes.data.data;

  // Store both tokens so the interceptor picks them up
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);

  // Fetch user profile
  const userRes = await api.get<APIResponse<User>>("/auth/me");
  const user = userRes.data.data;

  return { token: access_token, user };
}

export async function refreshTokenRequest(): Promise<string> {
  const refresh_token = localStorage.getItem("refresh_token");
  if (!refresh_token) {
    throw new Error("No refresh token available");
  }

  const res = await api.post<APIResponse<TokenResponse>>("/auth/refresh", {
    refresh_token,
  });
  const { access_token, refresh_token: new_refresh } = res.data.data;

  // Store new token pair
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
): Promise<APIResponse<User>> {
  const res = await api.post<APIResponse<User>>("/auth/register-requester", {
    email,
    password,
    full_name,
  });
  return res.data;
}
