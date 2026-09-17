/**
 * Same-origin `/api` proxy: the only way the browser reaches the API.
 *
 * 1. Strip every identity-bearing header the client may have sent.
 * 2. Resolve the principal (fixture in Phase A, built-in auth in Phase B).
 * 3. Enforce the anti-CSRF rules for state-changing requests.
 * 4. Issue a short-lived signed assertion and forward the request to FastAPI.
 */
import { serverConfig } from "@/lib/server/config";
import { issueAssertion } from "@/lib/server/assertion";
import { resolvePrincipal } from "@/lib/server/identity";
import { randomUUID } from "node:crypto";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const REQUEST_ID = /^[A-Za-z0-9._-]{8,64}$/;
const FORWARDED_REQUEST_HEADERS = ["content-type", "accept", "x-requested-with", "accept-language"];
const FORWARDED_RESPONSE_HEADERS = [
  "content-type",
  "content-length",
  "x-request-id",
  "x-response-time-ms",
  "x-audio-label",
  "x-audio-voice",
  "x-audio-asset-id",
  "cache-control",
  "www-authenticate",
];
const MAX_BODY_BYTES = 6 * 1024 * 1024;

type RouteContext = { params: Promise<{ path: string[] }> };

function json(status: number, body: Record<string, unknown>, requestId: string): Response {
  return new Response(JSON.stringify({ ...body, request_id: requestId }), {
    status,
    headers: { "content-type": "application/json", "x-request-id": requestId, "cache-control": "no-store" },
  });
}

function csrfViolation(request: Request): string | null {
  if (!UNSAFE.has(request.method.toUpperCase())) return null;
  if ((request.headers.get("x-requested-with") ?? "").toLowerCase() !== "fetch") {
    return "missing X-Requested-With header";
  }
  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite && fetchSite !== "same-origin" && fetchSite !== "none") {
    return `cross-site request (${fetchSite})`;
  }
  const origin = request.headers.get("origin");
  if (origin) {
    const own = new URL(request.url);
    let sent: URL;
    try {
      sent = new URL(origin);
    } catch {
      return "malformed Origin";
    }
    if (sent.host !== own.host) {
      return "Origin does not match this site";
    }
  }
  return null;
}

async function handle(request: Request, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const candidate = (request.headers.get("x-request-id") ?? "").trim();
  const requestId = REQUEST_ID.test(candidate) ? candidate : randomUUID().replace(/-/g, "");

  const config = serverConfig();
  const resolution = resolvePrincipal(request.headers, config);
  if (!resolution.ok) {
    return json(resolution.status, { detail: resolution.reason }, requestId);
  }
  const violation = csrfViolation(request);
  if (violation) {
    return json(403, { detail: `request refused: ${violation}` }, requestId);
  }

  const incoming = new URL(request.url);
  const target = `${config.apiInternalUrl}/${path.map(encodeURIComponent).join("/")}${incoming.search}`;

  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  headers.set("x-request-id", requestId);
  headers.set("authorization", `Bearer ${await issueAssertion(resolution.principal, requestId, config)}`);

  let body: ArrayBuffer | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.arrayBuffer();
    if (body.byteLength > MAX_BODY_BYTES) {
      return json(413, { detail: "request body too large" }, requestId);
    }
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, { method: request.method, headers, body, cache: "no-store", redirect: "manual" });
  } catch {
    return json(502, { detail: "the API is not reachable" }, requestId);
  }

  const responseHeaders = new Headers();
  for (const name of FORWARDED_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }
  responseHeaders.set("x-request-id", requestId);
  if (!responseHeaders.has("cache-control")) responseHeaders.set("cache-control", "no-store");
  return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export async function GET(request: Request, context: RouteContext) {
  return handle(request, context);
}
export async function POST(request: Request, context: RouteContext) {
  return handle(request, context);
}
export async function PUT(request: Request, context: RouteContext) {
  return handle(request, context);
}
export async function PATCH(request: Request, context: RouteContext) {
  return handle(request, context);
}
export async function DELETE(request: Request, context: RouteContext) {
  return handle(request, context);
}
