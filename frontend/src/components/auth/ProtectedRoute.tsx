import type { ReactNode } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

export interface ProtectedRouteProps {
  children?: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <main className="auth-page">
        <p>Loading session...</p>
      </main>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children ? <>{children}</> : <Outlet />;
}
