import { ApiError, type FastApiErrorBody } from "../types/auth";
import { getToken } from "../utils/tokenStorage";

const rawApiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const API_BASE_URL = rawApiUrl.replace(/\/+$/, "");

export interface ApiRequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean;
  token?: string;
  headers?: Record<string, string>;
}

function extractErrorMessage(body: FastApiErrorBody | null, status: number): string {
  if (body?.detail) {
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      return body.detail.map((item) => item.msg).join(". ");
    }
  }
  return `Request failed with status ${status}.`;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = false, token, headers = {} } = options;

  const requestHeaders: Record<string, string> = {
    Accept: "application/json",
    ...headers,
  };

  if (body !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
  }

  const bearerToken = token ?? (auth ? getToken() : null);
  if (bearerToken) {
    requestHeaders.Authorization = `Bearer ${bearerToken}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: requestHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Unable to reach the server. Please check your connection.", 0);
  }

  const text = await response.text();
  let parsedBody: unknown = null;
  if (text) {
    try {
      parsedBody = JSON.parse(text);
    } catch {
      parsedBody = null;
    }
  }

  if (!response.ok) {
    const errorBody =
      parsedBody && typeof parsedBody === "object" ? (parsedBody as FastApiErrorBody) : null;
    throw new ApiError(
      extractErrorMessage(errorBody, response.status),
      response.status,
      errorBody?.detail,
    );
  }

  return parsedBody as T;
}
