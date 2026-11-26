import { type ReactNode, useCallback, useEffect, useMemo, useState } from "react";

import * as authService from "../services/authService";
import {
  ApiError,
  type AuthUser,
  type LoginPayload,
  type RegisterPayload,
  isAuthResponse,
} from "../types/auth";
import { clearToken, getToken, setToken } from "../utils/tokenStorage";
import { AuthContext, type AuthContextValue, type RegisterResult } from "./authContext";

export interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [user, setUser] = useState<AuthUser | null>(null);
  const [hydratedToken, setHydratedToken] = useState<string | null>(null);

  const isLoading = Boolean(token && !user && hydratedToken !== token);

  useEffect(() => {
    if (!token || user || hydratedToken === token) {
      return;
    }

    let active = true;

    authService
      .getCurrentUser(token)
      .then((currentUser) => {
        if (active) {
          setUser(currentUser);
          setHydratedToken(token);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          clearToken();
          setTokenState(null);
          setUser(null);
        }
        setHydratedToken(token);
      });

    return () => {
      active = false;
    };
  }, [token, user, hydratedToken]);

  const login = useCallback(async (payload: LoginPayload): Promise<void> => {
    const response = await authService.login(payload);
    setToken(response.access_token);
    setTokenState(response.access_token);
    if (response.user) {
      setUser(response.user);
      setHydratedToken(response.access_token);
    } else {
      setUser(null);
      setHydratedToken(null);
    }
  }, []);

  const register = useCallback(async (payload: RegisterPayload): Promise<RegisterResult> => {
    const response = await authService.register(payload);
    if (isAuthResponse(response)) {
      setToken(response.access_token);
      setTokenState(response.access_token);
      if (response.user) {
        setUser(response.user);
        setHydratedToken(response.access_token);
      } else {
        setUser(null);
        setHydratedToken(null);
      }
      return { authenticated: true };
    }
    return { authenticated: false };
  }, []);

  const logout = useCallback((): void => {
    clearToken();
    setTokenState(null);
    setUser(null);
    setHydratedToken(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      isLoading,
      login,
      register,
      logout,
    }),
    [token, user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
