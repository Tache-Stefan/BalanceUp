import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { LoginForm } from "../components/auth/LoginForm";
import { useAuth } from "../hooks/useAuth";
import type { LoginPayload } from "../types/auth";

interface LoginLocationState {
  from?: { pathname: string };
  infoMessage?: string;
}

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LoginLocationState | null;

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleLogin = async (payload: LoginPayload) => {
    await login(payload);
    const destination = state?.from?.pathname || "/";
    navigate(destination, { replace: true });
  };

  return (
    <main className="auth-page">
      <section className="auth-card">
        <header className="auth-header">
          <h1>BalanceUp</h1>
          <p>Sign in to manage your budget and track your progress.</p>
        </header>

        <LoginForm onSubmit={handleLogin} infoMessage={state?.infoMessage} />

        <p className="auth-footer">
          Don&apos;t have an account? <Link to="/register">Create one</Link>
        </p>
      </section>
    </main>
  );
}
