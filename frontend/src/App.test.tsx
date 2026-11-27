import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { AppRoutes } from "./AppRoutes";
import { AuthProvider } from "./context/AuthProvider";
import { TOKEN_STORAGE_KEY } from "./utils/tokenStorage";

const sampleUser = {
  id: 1,
  email: "maria@example.com",
  display_name: "Maria",
  role: "user" as const,
  is_active: true,
  current_streak_days: 0,
  last_activity_date: null,
  created_at: "2026-11-26T12:00:00Z",
};

function renderWithRouter(initialEntries: string[] = ["/"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("App & Auth Routing", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the BalanceUp heading via App", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "BalanceUp" })).toBeInTheDocument();
  });

  it("redirects unauthenticated users from / to /login and lets them navigate to /register", () => {
    renderWithRouter(["/"]);

    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "Create one" }));
    expect(screen.getByRole("button", { name: "Create account" })).toBeInTheDocument();
  });

  it("logs in, stores JWT token, shows protected home page, and signs out", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (url: string) => {
        if (url.endsWith("/api/v1/auth/login")) {
          return {
            ok: true,
            status: 200,
            text: async () =>
              JSON.stringify({
                access_token: "jwt-123",
                token_type: "bearer",
                user: sampleUser,
              }),
          };
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({ status: "ok" }),
          text: async () => JSON.stringify({ status: "ok" }),
        };
      }),
    );

    renderWithRouter(["/login"]);

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "maria@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("button", { name: "Sign out" })).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBe("jwt-123");
    expect(screen.getByText(/Maria/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));

    expect(await screen.findByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });

  it("authenticates immediately when register returns a JWT token", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (url: string) => {
        if (url.endsWith("/api/v1/auth/register")) {
          return {
            ok: true,
            status: 201,
            text: async () =>
              JSON.stringify({
                access_token: "reg-jwt-456",
                token_type: "bearer",
                user: sampleUser,
              }),
          };
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({ status: "ok" }),
          text: async () => JSON.stringify({ status: "ok" }),
        };
      }),
    );

    renderWithRouter(["/register"]);

    fireEvent.change(screen.getByLabelText("Display name"), { target: { value: "Maria" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "maria@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByRole("button", { name: "Sign out" })).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBe("reg-jwt-456");
  });

  it("redirects to /login with info message when register does not return a JWT", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 201,
        text: async () => JSON.stringify(sampleUser),
      }),
    );

    renderWithRouter(["/register"]);

    fireEvent.change(screen.getByLabelText("Display name"), { target: { value: "Maria" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "maria@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByRole("status")).toHaveTextContent("Account created! Please sign in.");
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });

  it("clears token and redirects to /login when /auth/me returns 401", async () => {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, "expired-jwt");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ detail: "Token expired" }),
      }),
    );

    renderWithRouter(["/"]);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    });
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });
});
