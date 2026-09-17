/**
 * Server-only configuration for the web tier. Nothing here is exposed to the browser:
 * none of these variables carry the NEXT_PUBLIC_ prefix.
 */
import "server-only";

export type AppEnv = "development" | "test" | "production";

export interface ServerConfig {
  appEnv: AppEnv;
  devAuthEnabled: boolean;
  devOwnerEmail: string;
  devOwnerName: string;
  apiInternalUrl: string;
  assertionSigningKey: string;
  assertionIssuer: string;
  assertionAudience: string;
  assertionTtlSeconds: number;
}

function env(name: string, fallback = ""): string {
  const value = process.env[name];
  return value === undefined || value === "" ? fallback : value;
}

let cached: ServerConfig | null = null;

export function serverConfig(): ServerConfig {
  if (cached) return cached;
  const appEnv = (env("APP_ENV", "development") as AppEnv) || "development";
  const devAuthEnabled = env("DEV_AUTH_ENABLED", "false").toLowerCase() === "true";
  if (appEnv === "production" && devAuthEnabled) {
    throw new Error("DEV_AUTH_ENABLED must be false when APP_ENV=production");
  }
  const key = env("ASSERTION_SIGNING_KEY");
  if (appEnv === "production" && key.length < 32) {
    throw new Error("ASSERTION_SIGNING_KEY must be at least 32 characters in production");
  }
  cached = {
    appEnv,
    devAuthEnabled,
    devOwnerEmail: env("DEV_OWNER_EMAIL", "owner@example.com").toLowerCase(),
    devOwnerName: env("DEV_OWNER_NAME", "Owner"),
    apiInternalUrl: env("API_INTERNAL_URL", "http://127.0.0.1:8000").replace(/\/+$/, ""),
    assertionSigningKey: key,
    assertionIssuer: env("ASSERTION_ISSUER", "dlp-web"),
    assertionAudience: env("ASSERTION_AUDIENCE", "dlp-api"),
    assertionTtlSeconds: Number.parseInt(env("ASSERTION_TTL_SECONDS", "60"), 10) || 60,
  };
  return cached;
}
