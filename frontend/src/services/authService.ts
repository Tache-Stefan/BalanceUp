import type {
  AuthResponse,
  AuthUser,
  LoginPayload,
  RegisterPayload,
  RegisterResponse,
} from "../types/auth";
import { apiRequest } from "./api";

const AUTH_PREFIX = "/api/v1/auth";

export function login(payload: LoginPayload): Promise<AuthResponse> {
  return apiRequest<AuthResponse>(`${AUTH_PREFIX}/login`, {
    method: "POST",
    body: payload,
  });
}

export function register(payload: RegisterPayload): Promise<RegisterResponse> {
  return apiRequest<RegisterResponse>(`${AUTH_PREFIX}/register`, {
    method: "POST",
    body: payload,
  });
}

export function getCurrentUser(token?: string): Promise<AuthUser> {
  return apiRequest<AuthUser>(`${AUTH_PREFIX}/me`, {
    method: "GET",
    auth: true,
    token,
  });
}
