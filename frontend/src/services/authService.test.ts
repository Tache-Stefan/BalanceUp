import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../types/auth";
import { clearToken, setToken } from "../utils/tokenStorage";
import { API_BASE_URL } from "./api";
import { getCurrentUser, login, register } from "./authService";

function mockFetchResponse(body: unknown, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    text: async () => (body === undefined ? "" : JSON.stringify(body)),
  });
}

describe("authService", () => {
  beforeEach(() => {
    clearToken();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts credentials to /api/v1/auth/login and returns auth response", async () => {
    const fetchMock = mockFetchResponse({
      access_token: "abc.def.ghi",
      token_type: "bearer",
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await login({ email: "maria@example.com", password: "password123" });

    expect(result).toEqual({ access_token: "abc.def.ghi", token_type: "bearer" });
    expect(fetchMock).toHaveBeenCalledWith(`${API_BASE_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: "maria@example.com", password: "password123" }),
    });
  });

  it("posts registration payload to /api/v1/auth/register", async () => {
    const fetchMock = mockFetchResponse(
      {
        id: 1,
        email: "maria@example.com",
        display_name: "Maria",
        role: "user",
        is_active: true,
        current_streak_days: 0,
        last_activity_date: null,
        created_at: "2026-11-26T12:00:00Z",
      },
      201,
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await register({
      email: "maria@example.com",
      display_name: "Maria",
      password: "password123",
    });

    expect(result).toMatchObject({ email: "maria@example.com", display_name: "Maria" });
    expect(fetchMock).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/v1/auth/register`,
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("sends stored Bearer token when calling getCurrentUser", async () => {
    setToken("stored-jwt");
    const fetchMock = mockFetchResponse({
      id: 2,
      email: "maria@example.com",
      display_name: "Maria",
      role: "user",
      is_active: true,
      current_streak_days: 3,
      last_activity_date: "2026-11-26",
      created_at: "2026-11-20T12:00:00Z",
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = await getCurrentUser();

    expect(user.email).toBe("maria@example.com");
    expect(fetchMock).toHaveBeenCalledWith(`${API_BASE_URL}/api/v1/auth/me`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        Authorization: "Bearer stored-jwt",
      },
      body: undefined,
    });
  });

  it("throws ApiError with string detail from FastAPI", async () => {
    vi.stubGlobal("fetch", mockFetchResponse({ detail: "Invalid email or password" }, 401));

    await expect(login({ email: "maria@example.com", password: "wrong" })).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      message: "Invalid email or password",
    });
  });

  it("throws ApiError combining FastAPI 422 validation errors", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchResponse(
        {
          detail: [
            { loc: ["body", "email"], msg: "value is not a valid email address", type: "value" },
          ],
        },
        422,
      ),
    );

    await expect(login({ email: "bad", password: "password123" })).rejects.toThrow(
      "value is not a valid email address",
    );
  });

  it("throws ApiError with status 0 on network failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(
      login({ email: "maria@example.com", password: "password123" }),
    ).rejects.toBeInstanceOf(ApiError);
  });
});
