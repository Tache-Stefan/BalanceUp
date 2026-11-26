import { type FormEvent, useState } from "react";

import type { LoginPayload } from "../../types/auth";
import { type LoginFormErrors, validateLoginForm } from "../../utils/authValidation";
import "./auth.css";

export interface LoginFormProps {
  onSubmit: (payload: LoginPayload) => Promise<void>;
  infoMessage?: string | null;
}

export function LoginForm({ onSubmit, infoMessage }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<LoginFormErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const errors = validateLoginForm({ email, password });
    setFieldErrors(errors);
    setServerError(null);

    if (Object.keys(errors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        email: email.trim(),
        password,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to sign in. Please try again.";
      setServerError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      {infoMessage && (
        <div className="auth-alert auth-alert--info" role="status">
          {infoMessage}
        </div>
      )}

      {serverError && (
        <div className="auth-alert auth-alert--error" role="alert">
          {serverError}
        </div>
      )}

      <div className="auth-field">
        <label htmlFor="login-email">Email</label>
        <input
          id="login-email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          disabled={isSubmitting}
          aria-invalid={Boolean(fieldErrors.email)}
          aria-describedby={fieldErrors.email ? "login-email-error" : undefined}
          onChange={(event) => {
            setEmail(event.target.value);
            if (fieldErrors.email) {
              setFieldErrors((prev) => ({ ...prev, email: undefined }));
            }
          }}
        />
        {fieldErrors.email && (
          <p id="login-email-error" className="auth-field-error">
            {fieldErrors.email}
          </p>
        )}
      </div>

      <div className="auth-field">
        <label htmlFor="login-password">Password</label>
        <input
          id="login-password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          disabled={isSubmitting}
          aria-invalid={Boolean(fieldErrors.password)}
          aria-describedby={fieldErrors.password ? "login-password-error" : undefined}
          onChange={(event) => {
            setPassword(event.target.value);
            if (fieldErrors.password) {
              setFieldErrors((prev) => ({ ...prev, password: undefined }));
            }
          }}
        />
        {fieldErrors.password && (
          <p id="login-password-error" className="auth-field-error">
            {fieldErrors.password}
          </p>
        )}
      </div>

      <button type="submit" className="auth-submit-btn" disabled={isSubmitting}>
        {isSubmitting ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}
