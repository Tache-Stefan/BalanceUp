import { beforeEach, describe, expect, it } from "vitest";

import { TOKEN_STORAGE_KEY, clearToken, getToken, setToken } from "./tokenStorage";

describe("tokenStorage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns null when no token is stored", () => {
    expect(getToken()).toBeNull();
  });

  it("stores and retrieves the JWT token", () => {
    setToken("jwt-token-123");
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBe("jwt-token-123");
    expect(getToken()).toBe("jwt-token-123");
  });

  it("clears the stored token", () => {
    setToken("jwt-token-123");
    clearToken();
    expect(getToken()).toBeNull();
  });
});
