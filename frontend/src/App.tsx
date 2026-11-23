import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [apiStatus, setApiStatus] = useState<string>("checking...");

  useEffect(() => {
    let active = true;

    fetch(`${API_URL}/api/v1/health`)
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
      <h1>BalanceUp</h1>
      <p>Personal finance, budgeting, and gamified savings platform.</p>
      <p>
        Backend API status: <strong>{apiStatus}</strong>
      </p>
    </main>
  );
}

export default App;
