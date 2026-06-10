import api from "./api";
import type { TokenResponse, User, APIResponse } from "../types";

export async function loginRequest(
  email: string,
  password: string
): Promise<{ token: string; user: User }> {
  // Login endpoint returns TokenResponse
  const tokenRes = await api.post<APIResponse<TokenResponse>>("/auth/login", {
    email,
    password,
  });
  const token = tokenRes.data.data.access_token;

  // Store token so the interceptor picks it up for /me
  localStorage.setItem("access_token", token);

  // Fetch user profile
  const userRes = await api.get<APIResponse<User>>("/auth/me");
  const user = userRes.data.data;

  return { token, user };
}

export async function registerRequesterRequest(
  email: string,
  password: string,
  fullName: string
): Promise<void> {
  await api.post("/auth/register-requester", {
    email,
    password,
    full_name: fullName,
  });
}
