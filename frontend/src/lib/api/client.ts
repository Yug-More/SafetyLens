import type {
  ApiCollectionResponse,
  ApiErrorPayload,
  ApiItemResponse,
} from "@/lib/api/types";

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

export function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_URL?.trim();
  return base && base.length > 0 ? base.replace(/\/$/, "") : "http://localhost:8000";
}

export function isDemoFallbackEnabled(): boolean {
  const value = process.env.NEXT_PUBLIC_DEMO_FALLBACK?.trim().toLowerCase();
  return value === undefined || value === "" || value === "true" || value === "1";
}

function buildUrl(path: string, query?: Record<string, string | number | boolean | undefined>) {
  const url = new URL(path, `${getApiBaseUrl()}/`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    if (payload?.error?.code && payload?.error?.message) {
      return new ApiError(payload.error.code, payload.error.message, response.status);
    }
  } catch {
    // fall through
  }
  return new ApiError(
    "HTTP_ERROR",
    `Request failed with status ${response.status}`,
    response.status
  );
}

export async function apiGetItem<T>(
  path: string,
  query?: Record<string, string | number | boolean | undefined>,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(buildUrl(path, query), {
    ...init,
    method: "GET",
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  const payload = (await response.json()) as ApiItemResponse<T>;
  return payload.data;
}

export async function apiGetCollection<T>(
  path: string,
  query?: Record<string, string | number | boolean | undefined>,
  init?: RequestInit
): Promise<ApiCollectionResponse<T>> {
  const response = await fetch(buildUrl(path, query), {
    ...init,
    method: "GET",
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  return (await response.json()) as ApiCollectionResponse<T>;
}
