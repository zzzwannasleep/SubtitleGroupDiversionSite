const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";


interface RequestOptions {
  method?: string;
  body?: BodyInit | Record<string, unknown> | null;
  headers?: HeadersInit;
  auth?: boolean;
}


interface StructuredApiError {
  code?: string;
  message?: string;
  status_code?: number;
  request_id?: string;
  details?: unknown;
}


export class ApiError extends Error {
  status: number;
  code?: string;
  requestId?: string;
  details?: unknown;

  constructor(message: string, status: number, options: { code?: string; requestId?: string; details?: unknown } = {}) {
    super(message);
    this.status = status;
    this.code = options.code;
    this.requestId = options.requestId;
    this.details = options.details;
  }
}


function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}


function readStructuredError(payload: unknown): StructuredApiError {
  if (!isRecord(payload)) {
    return {};
  }

  if (isRecord(payload.error)) {
    return {
      code: typeof payload.error.code === "string" ? payload.error.code : undefined,
      message: typeof payload.error.message === "string" ? payload.error.message : undefined,
      status_code: typeof payload.error.status_code === "number" ? payload.error.status_code : undefined,
      request_id: typeof payload.error.request_id === "string" ? payload.error.request_id : undefined,
      details: payload.error.details,
    };
  }

  if (typeof payload.detail === "string") {
    return { message: payload.detail };
  }

  if (typeof payload.message === "string") {
    return { message: payload.message };
  }

  if (Array.isArray(payload.detail)) {
    return { message: "Request validation failed", details: payload.detail };
  }

  return {};
}


export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = localStorage.getItem("pt-platform.token");

  if (options.auth !== false && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let body = options.body;
  if (body && !(body instanceof FormData) && typeof body !== "string") {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: body as BodyInit | null | undefined,
  });

  if (!response.ok) {
    let message = "Request failed";
    let code: string | undefined;
    let requestId = response.headers.get("X-Request-ID") ?? undefined;
    let details: unknown;

    try {
      const payload = await response.json();
      const structuredError = readStructuredError(payload);
      message = structuredError.message ?? message;
      code = structuredError.code;
      requestId = structuredError.request_id ?? requestId;
      details = structuredError.details;
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(message, response.status, { code, requestId, details });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
