type PrimitiveQueryValue = string | number | boolean | null | undefined;
type QueryValue = PrimitiveQueryValue | PrimitiveQueryValue[];

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message: string;
  code?: string;
  errors?: unknown;
}

interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  body?: BodyInit | FormData | object | null;
  query?: Record<string, QueryValue> | object;
}

export class ApiError extends Error {
  status: number;
  code: string;
  errors?: unknown;

  constructor(message: string, status: number, code = 'request_error', errors?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.errors = errors;
  }
}

function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
}

export function buildApiUrl(path: string, query?: Record<string, QueryValue> | object) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const baseUrl = getApiBaseUrl();
  const url = new URL(baseUrl ? `${baseUrl}${normalizedPath}` : normalizedPath, window.location.origin);

  if (query) {
    for (const [key, value] of Object.entries(query as Record<string, QueryValue>)) {
      if (Array.isArray(value)) {
        for (const item of value) {
          if (item !== undefined && item !== null && item !== '') {
            url.searchParams.append(key, String(item));
          }
        }
        continue;
      }

      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    }
  }

  return url.toString();
}

async function parseResponseBody(response: Response) {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

function isHtmlErrorDocument(payload: string) {
  return /^\s*<!doctype html/i.test(payload) || /^\s*<html[\s>]/i.test(payload);
}

function getFallbackErrorMessage(response: Response, payload: unknown) {
  if (typeof payload === 'string') {
    const normalized = payload.trim();
    if (normalized && !isHtmlErrorDocument(normalized)) {
      return normalized;
    }
  }

  if (response.status >= 500) {
    return `服务暂时不可用（HTTP ${response.status}）。`;
  }

  return `请求失败（HTTP ${response.status}）。`;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  let body: BodyInit | null | undefined = null;

  if (options.body instanceof FormData) {
    body = options.body;
  } else if (
    options.body &&
    typeof options.body === 'object' &&
    !(options.body instanceof Blob) &&
    !(options.body instanceof URLSearchParams)
  ) {
    headers.set('Content-Type', 'application/json');
    body = JSON.stringify(options.body);
  } else {
    body = options.body ?? null;
  }

  const response = await fetch(buildApiUrl(path, options.query), {
    ...options,
    body,
    headers,
    credentials: 'include',
  });

  const payload = await parseResponseBody(response);

  if (!response.ok) {
    if (typeof payload === 'object' && payload && 'message' in payload) {
      const errorPayload = payload as Partial<ApiEnvelope<unknown>>;
      throw new ApiError(
        String(errorPayload.message ?? `请求失败（HTTP ${response.status}）。`),
        response.status,
        String(errorPayload.code ?? 'request_error'),
        errorPayload.errors,
      );
    }

    throw new ApiError(getFallbackErrorMessage(response, payload), response.status);
  }

  if (typeof payload !== 'object' || !payload || !('success' in payload)) {
    throw new ApiError('接口响应格式无效。', response.status);
  }

  return (payload as ApiEnvelope<T>).data;
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
