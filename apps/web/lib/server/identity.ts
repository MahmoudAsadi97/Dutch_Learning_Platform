/**
 * Identity providers for the web tier, the only public entry point.
 *
 * - fixture:  Phase A. Enabled only when APP_ENV=development and DEV_AUTH_ENABLED=true,
 *             and only for requests addressed to localhost.
 * - easyauth: Phase B. Container Apps built-in authentication injects the
 *             X-MS-CLIENT-PRINCIPAL headers after it has authenticated the caller.
 *             The web container must be reachable only through that sidecar.
 *
 * Whatever the provider, the browser never supplies identity: the proxy strips
 * client-sent identity headers before this code runs.
 */
import "server-only";

import { serverConfig, type ServerConfig } from "./config";

export type IdentityProvider = "fixture" | "easyauth";

export interface Principal {
  subject: string;
  email: string;
  name: string;
  identityProvider: IdentityProvider;
}

export type Resolution =
  | { ok: true; principal: Principal }
  | { ok: false; status: number; reason: string };

const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

function isLocalHost(hostHeader: string | null): boolean {
  if (!hostHeader) return false;
  const host = hostHeader.replace(/:\d+$/, "").toLowerCase();
  return LOCAL_HOSTS.has(host);
}

interface EasyAuthClaim {
  typ: string;
  val: string;
}

interface EasyAuthPrincipal {
  auth_typ?: string;
  claims?: EasyAuthClaim[];
  name_typ?: string;
}

const EMAIL_CLAIMS = [
  "preferred_username",
  "email",
  "emails",
  "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
  "upn",
];
const NAME_CLAIMS = ["name", "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"];

function fromEasyAuth(headers: Headers): Resolution {
  const encoded = headers.get("x-ms-client-principal");
  const id = headers.get("x-ms-client-principal-id") ?? "";
  if (!encoded || !id) {
    return { ok: false, status: 401, reason: "not authenticated" };
  }
  let parsed: EasyAuthPrincipal;
  try {
    parsed = JSON.parse(Buffer.from(encoded, "base64").toString("utf8")) as EasyAuthPrincipal;
  } catch {
    return { ok: false, status: 401, reason: "unreadable principal" };
  }
  const claims = parsed.claims ?? [];
  const find = (types: string[]) => claims.find((claim) => types.includes(claim.typ))?.val ?? "";
  const email = find(EMAIL_CLAIMS).toLowerCase();
  if (!email) {
    return { ok: false, status: 401, reason: "principal has no email claim" };
  }
  return {
    ok: true,
    principal: { subject: id, email, name: find(NAME_CLAIMS), identityProvider: "easyauth" },
  };
}

export function resolvePrincipal(headers: Headers, config: ServerConfig = serverConfig()): Resolution {
  if (config.devAuthEnabled) {
    if (config.appEnv !== "development") {
      return { ok: false, status: 500, reason: "fixture identity outside development" };
    }
    if (!isLocalHost(headers.get("host"))) {
      return { ok: false, status: 403, reason: "fixture identity is bound to localhost" };
    }
    return {
      ok: true,
      principal: {
        subject: `fixture:${config.devOwnerEmail}`,
        email: config.devOwnerEmail,
        name: config.devOwnerName,
        identityProvider: "fixture",
      },
    };
  }
  return fromEasyAuth(headers);
}
