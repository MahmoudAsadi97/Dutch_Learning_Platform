import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "./api";

/**
 * One query client per browser tab (created in app/providers.tsx).
 *
 * - Data is fresh for 30 s, so sibling components sharing a key make one request.
 * - No refetch on window focus: a learner switching tabs mid-exercise must not see state jump.
 * - A query is retried only when the API said it is temporarily unavailable (503) or the proxy timed
 *   out waiting for it (504); a 4xx is an answer, not a hiccup.
 * - Mutations are never retried automatically: every POST carries a request id and the caller decides.
 */
const RETRYABLE = new Set([503, 504]);

export function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  if (failureCount >= 2) return false;
  return error instanceof ApiError && RETRYABLE.has(error.status);
}

export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: shouldRetryQuery,
        retryDelay: (attempt) => Math.min(1_000 * 2 ** attempt, 5_000),
      },
      mutations: { retry: false },
    },
  });
}
