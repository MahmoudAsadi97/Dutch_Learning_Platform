import "server-only";

import { randomUUID } from "node:crypto";
import { headers } from "next/headers";

import type { Me } from "@/lib/client/profile";
import { issueAssertion } from "./assertion";
import { serverConfig } from "./config";
import { resolvePrincipal } from "./identity";

/** The first paint waits at most this long for the profile; after that the page renders without it. */
const PREFETCH_TIMEOUT_MS = 1500;

/**
 * The learner's profile for the first render, fetched the way the /api proxy forwards a request: the same
 * principal, a fresh signed assertion, the internal API address. Any failure returns null and the client
 * loads /me itself, so the prefetch can only make the first paint better, never block it.
 */
export async function prefetchMe(): Promise<Me | null> {
  try {
    const config = serverConfig();
    const resolution = resolvePrincipal(await headers(), config);
    if (!resolution.ok) return null;
    const requestId = randomUUID().replace(/-/g, "");
    const response = await fetch(`${config.apiInternalUrl}/me`, {
      headers: {
        accept: "application/json",
        authorization: `Bearer ${await issueAssertion(resolution.principal, requestId, config)}`,
        "x-request-id": requestId,
      },
      cache: "no-store",
      signal: AbortSignal.timeout(PREFETCH_TIMEOUT_MS),
    });
    if (!response.ok) return null;
    return (await response.json()) as Me;
  } catch {
    return null;
  }
}
