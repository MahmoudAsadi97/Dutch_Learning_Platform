/**
 * Browser-side helper for calling the same-origin `/api` proxy.
 * Adds the anti-CSRF header, a request id (kept stable across retries when given), and JSON handling.
 */

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
    public readonly requestId: string,
  ) {
    super(`${status}: ${detail}`);
  }
}

export function newRequestId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return `r${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`;
}

export interface ApiOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  formData?: FormData;
  requestId?: string;
  signal?: AbortSignal;
}

/** Name of the DOM event fired on `window` when a call could not reach the server or reached it again. */
export const CONNECTIVITY_EVENT = "dlp:connectivity";

function announce(reachable: boolean) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(CONNECTIVITY_EVENT, { detail: { reachable } }));
}

export async function apiFetch(path: string, options: ApiOptions = {}): Promise<Response> {
  const headers: Record<string, string> = {
    "X-Requested-With": "fetch",
    "X-Request-Id": options.requestId ?? newRequestId(),
    Accept: "application/json, audio/wav",
  };
  let body: BodyInit | undefined;
  if (options.formData) {
    body = options.formData;
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }
  let response: Response;
  try {
    response = await fetch(`/api/${path.replace(/^\/+/, "")}`, {
      method: options.method ?? "GET",
      headers,
      body,
      signal: options.signal,
      cache: "no-store",
      credentials: "same-origin",
    });
  } catch (cause) {
    if (!(cause instanceof DOMException && cause.name === "AbortError")) announce(false);
    throw cause;
  }
  // 502 from the proxy means the web tier is up but the API is not; anything else proves the path works.
  announce(response.status !== 502);
  return response;
}

export async function apiJson<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const response = await apiFetch(path, options);
  const requestId = response.headers.get("x-request-id") ?? "";
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : response.statusText;
    throw new ApiError(response.status, detail, requestId);
  }
  return payload as T;
}
