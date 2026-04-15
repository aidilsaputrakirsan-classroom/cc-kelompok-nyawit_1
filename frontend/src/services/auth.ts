import api from "./api";
import type { TokenResponse, User, APIResponse } from "../types";

export async function loginRequest(
  email: string,
  password: string
): Promise<{ token: string; user: User }> {
  const tokenRes = await api.post<TokenResponse | APIResponse<TokenResponse>>("/auth/login", {
    email,
    password,
  });
  const tokenPayload =
    "data" in tokenRes.data ? tokenRes.data.data : tokenRes.data;
  const token = tokenPayload.access_token;

  // Store token so the interceptor picks it up for /me
  localStorage.setItem("access_token", token);

  // Fetch user profile
  const userRes = await api.get<User | APIResponse<User>>("/auth/me");
  const user = "data" in userRes.data ? userRes.data.data : userRes.data;

  return { token, user };
}
