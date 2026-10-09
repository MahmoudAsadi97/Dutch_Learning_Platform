import type { Copy } from "@/lib/ui-copy";

/**
 * The learner-facing message for a failed call, chosen from the API's stable error code first and the
 * HTTP status second, so one place decides what every screen says. Pure and free of runtime imports, so
 * the node:test suite loads it; callers pass the catalogue's `errors` group.
 */
export interface ErrorCopies {
  generic: Copy;
  offline: Copy;
  serverAway: Copy;
  session: Copy;
  forbidden: Copy;
  notFound: Copy;
  tooLarge: Copy;
  invalid: Copy;
  limit: Copy;
  modelAway: Copy;
  episodesBusy: Copy;
  videosBusy: Copy;
  notReady: Copy;
  alreadyAnswered: Copy;
  sessionClosed: Copy;
  turnLimit: Copy;
  noRetry: Copy;
  inProgress: Copy;
  evidenceShort: Copy;
}

/** The API's error codes that read the same on every screen; the API's English `detail` is never shown. */
const BY_CODE: Record<string, keyof ErrorCopies> = {
  usage_limit: "limit",
  provider_unavailable: "modelAway",
  provider_failed: "modelAway",
  episodes_busy: "episodesBusy",
  videos_busy: "videosBusy",
  not_ready: "notReady",
  already_answered: "alreadyAnswered",
  session_closed: "sessionClosed",
  turn_limit: "turnLimit",
  no_retry: "noRetry",
  in_progress: "inProgress",
  evidence_short: "evidenceShort",
};

const BY_STATUS: Record<number, keyof ErrorCopies> = {
  401: "session",
  403: "forbidden",
  404: "notFound",
  413: "tooLarge",
  422: "invalid",
  429: "limit",
  502: "serverAway",
  503: "modelAway",
  504: "serverAway",
};

/** What a failed call looks like to this module: an ApiError has a status and, from the API, a code. */
interface FailedCall {
  status?: unknown;
  code?: unknown;
  name?: unknown;
}

/** A screen may say something more precise for a code or a status (a final check's 403, for example). */
export type ErrorOverrides = Partial<Record<string | number, Copy>>;

export function errorFor(cause: unknown, copies: ErrorCopies, overrides: ErrorOverrides = {}): Copy {
  const failed = (typeof cause === "object" && cause !== null ? cause : {}) as FailedCall;
  const status = typeof failed.status === "number" ? failed.status : undefined;
  const code = typeof failed.code === "string" ? failed.code : "";
  // fetch rejects with a TypeError when the network is gone; the proxy answers 502/504 when the API is
  if (status === undefined) return failed.name === "TypeError" ? copies.offline : copies.generic;
  const own = (key: string | number) => Object.hasOwn(overrides, key) && overrides[key];
  if (code && own(code)) return overrides[code]!;
  if (own(status)) return overrides[status]!;
  if (Object.hasOwn(BY_CODE, code)) return copies[BY_CODE[code]];
  if (Object.hasOwn(BY_STATUS, status)) return copies[BY_STATUS[status]];
  return copies.generic;
}

/** True when the call was cancelled on purpose (navigation, a newer request); nothing to tell the learner. */
export function isAbort(cause: unknown): boolean {
  return typeof cause === "object" && cause !== null && (cause as { name?: unknown }).name === "AbortError";
}
