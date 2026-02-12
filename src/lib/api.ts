import type { ErrorResponse } from "../types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiRequestError extends Error {
  status: number;
  payload: ErrorResponse | null;

  constructor(status: number, payload: ErrorResponse | null) {
    super(payload?.message ?? `Request failed with status ${status}`);
    this.name = "ApiRequestError";
    this.status = status;
    this.payload = payload;
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let payload: ErrorResponse | null = null;
    try {
      payload = (await response.json()) as ErrorResponse;
    } catch {
      payload = null;
    }
    throw new ApiRequestError(response.status, payload);
  }

  return (await response.json()) as T;
}
