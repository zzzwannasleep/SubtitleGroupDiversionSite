const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";


interface RequestOptions {
  method?: string;
  body?: BodyInit | Record<string, unknown> | null;
  headers?: HeadersInit;
  auth?: boolean;
}


export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
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
    try {
      const payload = await response.json();
      message = payload.detail ?? payload.message ?? message;
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

