import { createContext } from "react";

import type { AuthUser, LoginPayload, RegisterPayload } from "../types/auth";

export interface RegisterResult {
  authenticated: boolean;
}

export interface AuthContextValue {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<RegisterResult>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
