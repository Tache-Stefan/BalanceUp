import { type FormEvent, useState } from "react";

import type { RegisterPayload } from "../../types/auth";
import { type RegisterFormErrors, validateRegisterForm } from "../../utils/authValidation";
import "./auth.css";

export interface RegisterFormProps {
  onSubmit: (payload: RegisterPayload) => Promise<void>;
}

export function RegisterForm({ onSubmit }: RegisterFormProps) {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<RegisterFormErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const errors = validateRegisterForm({
      displayName,
      email,
      password,
      confirmPassword,
    });
    setFieldErrors(errors);
    setServerError(null);

    if (Object.keys(errors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        display_name: displayName.trim(),
        email: email.trim(),
        password,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to create account. Please try again.";
      setServerError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      {serverError && (
        <div className="auth-alert auth-alert--error" role="alert">
          {serverError}
        </div>
      )}

      <div className="auth-field">
        <label htmlFor="register-display-name">Display name</label>
        <input
          id="register-display-name"
          name="displayName"
          type="text"
          autoComplete="name"
          value={displayName}
          disabled={isSubmitting}
          aria-invalid={Boolean(fieldErrors.displayName)}
          aria-describedby={fieldErrors.displayName ? "register-display-name-error" : undefined}
          onChange={(event) => {
            setDisplayName(event.target.value);
            if (fieldErrors.displayName) {
              setFieldErrors((prev) => ({ ...prev, displayName: undefined }));
            }
          }}
        />
        {fieldErrors.displayName && (
          <p id="register-display-name-error" className="auth-field-error">
            {fieldErrors.displayName}
          </p>
        )}
      </div>

      <div className="auth-field">
        <label htmlFor="register-email">Email</label>
        <input
          id="register-email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          disabled={isSubmitting}
          aria-invalid={Boolean(fieldErrors.email)}
          aria-describedby={fieldErrors.email ? "register-email-error" : undefined}
          onChange={(event) => {
            setEmail(event.target.value);
            if (fieldErrors.email) {
              setFieldErrors((prev) => ({ ...prev, email: undefined }));
            }
          }}
        />
        {fieldErrors.email && (
          <p id="register-email-error" className="auth-field-error">
            {fieldErrors.email}
          </p>
        )}
      </div>

      <div className="auth-field">
        <label htmlFor="register-password">Password</label>
        <input
          id="register-password"
          name="password"
          type="password"
          autoComplete="new-password"
          value={password}
          disabled={isSubmitting}
          aria-invalid={Boolean(fieldErrors.password)}
          aria-describedby={fieldErrors.password ? "register-password-error" : undefined}
          onChange={(event) => {
            setPassword(event.target.value);
            if (fieldErrors.password) {
              setFieldErrors((prev) => ({ ...prev, password: undefined }));
            }
          }}
        />
        {fieldErrors.password && (
          <p id="register-password-error" className="auth-field-error">
            {fieldErrors.password}
          </p>
        )}
      </div>

      <div className="auth-field">
        <label htmlFor="register-confirm-password">Confirm password</label>
        <input
          id="register-confirm-password"
          name="confirmPassword"
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          disabled={isSubmitting}
          aria-invalid={Boolean(fieldErrors.confirmPassword)}
          aria-describedby={
            fieldErrors.confirmPassword ? "register-confirm-password-error" : undefined
          }
          onChange={(event) => {
            setConfirmPassword(event.target.value);
            if (fieldErrors.confirmPassword) {
              setFieldErrors((prev) => ({ ...prev, confirmPassword: undefined }));
            }
          }}
        />
        {fieldErrors.confirmPassword && (
          <p id="register-confirm-password-error" className="auth-field-error">
            {fieldErrors.confirmPassword}
          </p>
        )}
      </div>

      <button type="submit" className="auth-submit-btn" disabled={isSubmitting}>
        {isSubmitting ? "Creating account..." : "Create account"}
      </button>
    </form>
  );
}
