import { randomBytes } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

/** Fresh per-response script nonce. Fonts, media and API traffic stay on this origin. */
export function proxy(request: NextRequest) {
  const nonce = randomBytes(24).toString("base64");
  const development = process.env.NODE_ENV === "development";
  const policy = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${development ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self'",
    "img-src 'self' data: blob:",
    "media-src 'self' blob:",
    `connect-src 'self'${development ? " ws: wss:" : ""}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");
  const headers = new Headers(request.headers);
  headers.set("x-nonce", nonce);
  headers.set("Content-Security-Policy", policy);
  const response = NextResponse.next({ request: { headers } });
  response.headers.set("Content-Security-Policy", policy);
  response.headers.set("Cache-Control", "private, no-store");
  if (process.env.APP_ENV === "production") {
    response.headers.set("Strict-Transport-Security", "max-age=31536000");
  }
  return response;
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|health).*)"],
};
