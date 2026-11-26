import { useEffect, useState } from "react";

import "../components/auth/auth.css";
import { useAuth } from "../hooks/useAuth";
import { API_BASE_URL } from "../services/api";

export function HomePage() {
  const { user, logout } = useAuth();
  const [apiStatus, setApiStatus] = useState<string>("checking...");

  useEffect(() => {
    let active = true;

    fetch(`${API_BASE_URL}/api/v1/health`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`HTTP ${res.status}`))))
      .then((data: { status?: string }) => {
        if (active) {
          setApiStatus(data.status ?? "ok");
        }
      })
      .catch(() => {
        if (active) {
          setApiStatus("unavailable");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <main style={{ maxWidth: 640, margin: "4rem auto", padding: "0 1.5rem" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "1rem",
        }}
      >
        <h1 style={{ margin: 0 }}>BalanceUp</h1>
        <button type="button" className="auth-submit-btn" onClick={logout}>
          Sign out
        </button>
      </header>

      <p>Personal finance, budgeting, and gamified savings platform.</p>

      {user ? (
        <p>
          Signed in as <strong>{user.display_name}</strong> ({user.email}) &middot; Role:{" "}
          <strong>{user.role}</strong>
        </p>
      ) : (
        <p>Signed in with an active session token.</p>
      )}

      <p>
        Backend API status: <strong>{apiStatus}</strong>
      </p>
    </main>
  );
}
