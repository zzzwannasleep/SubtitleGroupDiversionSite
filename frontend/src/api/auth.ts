import type { AuthUser } from "@/types";

import { apiRequest } from "./http";


export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}


export function login(payload: LoginPayload): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: payload,
    auth: false,
  });
}


export function register(payload: RegisterPayload): Promise<{ id: number; username: string; email: string; role: string }> {
  return apiRequest("/auth/register", {
    method: "POST",
    body: payload,
    auth: false,
  });
}


export function getCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me");
}

