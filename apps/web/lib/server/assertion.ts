/**
 * Issues the short-lived assertion the API requires on every request.
 * HS256 with a server-only shared key; explicit issuer, audience and expiry; one jti per request.
 */
import "server-only";

import { randomUUID } from "node:crypto";
import { SignJWT } from "jose";

import { serverConfig, type ServerConfig } from "./config";
import type { Principal } from "./identity";

const encoder = new TextEncoder();

export async function issueAssertion(
  principal: Principal,
  requestId: string,
  config: ServerConfig = serverConfig(),
): Promise<string> {
  if (config.assertionSigningKey.length < 32) {
    throw new Error("ASSERTION_SIGNING_KEY is not configured (at least 32 characters)");
  }
  const now = Math.floor(Date.now() / 1000);
  return new SignJWT({
    email: principal.email,
    name: principal.name,
    idp: principal.identityProvider,
    rid: requestId,
  })
    .setProtectedHeader({ alg: "HS256", typ: "JWT" })
    .setIssuer(config.assertionIssuer)
    .setAudience(config.assertionAudience)
    .setSubject(principal.subject)
    .setJti(randomUUID())
    .setIssuedAt(now)
    .setNotBefore(now - 5)
    .setExpirationTime(now + config.assertionTtlSeconds)
    .sign(encoder.encode(config.assertionSigningKey));
}
