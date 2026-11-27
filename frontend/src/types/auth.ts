export type UserRole = "user" | "moderator" | "admin";

export interface AuthUser {
  id: number;
  email: string;
  display_name: string;
  role: UserRole;
  is_active: boolean;
  current_streak_days: number;
  last_activity_date: string | null;
  created_at: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  display_name: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user?: AuthUser;
}

export type RegisterResponse = AuthResponse | AuthUser;

export function isAuthResponse(response: RegisterResponse): response is AuthResponse {
  return (
    typeof (response as AuthResponse).access_token === "string" &&
    (response as AuthResponse).access_token.length > 0
  );
}

export interface FastApiValidationErrorItem {
  loc: Array<string | number>;
  msg: string;
  type: string;
}

export interface FastApiErrorBody {
  detail?: string | FastApiValidationErrorItem[];
}

export class ApiError extends Error {
  readonly status: number;
  readonly detail?: string | FastApiValidationErrorItem[];

  constructor(message: string, status: number, detail?: string | FastApiValidationErrorItem[]) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}
