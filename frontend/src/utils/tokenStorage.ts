export const TOKEN_STORAGE_KEY = "balanceup_access_token";

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch {
    // Ignore storage errors (e.g., private mode quota limits)
  }
}

export function clearToken(): void {
  try {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // Ignore storage errors
  }
}
