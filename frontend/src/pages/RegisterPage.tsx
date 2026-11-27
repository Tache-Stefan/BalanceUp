import { Link, Navigate, useNavigate } from "react-router-dom";

import { RegisterForm } from "../components/auth/RegisterForm";
import { useAuth } from "../hooks/useAuth";
import type { RegisterPayload } from "../types/auth";

export function RegisterPage() {
  const { isAuthenticated, register } = useAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleRegister = async (payload: RegisterPayload) => {
    const result = await register(payload);
    if (result.authenticated) {
      navigate("/", { replace: true });
    } else {
      navigate("/login", {
        replace: true,
        state: { infoMessage: "Account created! Please sign in." },
      });
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-card">
        <header className="auth-header">
          <h1>BalanceUp</h1>
          <p>Create your account to start tracking your finances.</p>
        </header>

        <RegisterForm onSubmit={handleRegister} />

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
