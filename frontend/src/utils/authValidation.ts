const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export interface LoginFormValues {
  email: string;
  password: string;
}

export interface LoginFormErrors {
  email?: string;
  password?: string;
}

export interface RegisterFormValues {
  displayName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface RegisterFormErrors {
  displayName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

export function isValidEmail(email: string): boolean {
  const trimmed = email.trim();
  return trimmed.length <= 255 && EMAIL_REGEX.test(trimmed);
}

export function validateLoginForm(values: LoginFormValues): LoginFormErrors {
  const errors: LoginFormErrors = {};
  const trimmedEmail = values.email.trim();

  if (!trimmedEmail) {
    errors.email = "Email is required.";
  } else if (!isValidEmail(trimmedEmail)) {
    errors.email = "Please enter a valid email address.";
  }

  if (!values.password) {
    errors.password = "Password is required.";
  }

  return errors;
}

export function validateRegisterForm(values: RegisterFormValues): RegisterFormErrors {
  const errors: RegisterFormErrors = {};
  const trimmedName = values.displayName.trim();
  const trimmedEmail = values.email.trim();

  if (!trimmedName) {
    errors.displayName = "Display name is required.";
  } else if (trimmedName.length < 2) {
    errors.displayName = "Display name must be at least 2 characters.";
  } else if (trimmedName.length > 100) {
    errors.displayName = "Display name must be at most 100 characters.";
  }

  if (!trimmedEmail) {
    errors.email = "Email is required.";
  } else if (!isValidEmail(trimmedEmail)) {
    errors.email = "Please enter a valid email address.";
  }

  if (!values.password) {
    errors.password = "Password is required.";
  } else if (values.password.length < 8) {
    errors.password = "Password must be at least 8 characters.";
  }

  if (!values.confirmPassword) {
    errors.confirmPassword = "Please confirm your password.";
  } else if (values.confirmPassword !== values.password) {
    errors.confirmPassword = "Passwords do not match.";
  }

  return errors;
}
