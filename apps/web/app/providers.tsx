"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import type { Me } from "@/lib/client/profile";
import { makeQueryClient } from "@/lib/client/query-client";
import { queryKeys } from "@/lib/client/query-keys";

/**
 * Client-side providers for the whole app: the query cache (server state lives here, not in useState).
 * The profile the server fetched for the first render seeds the cache, so nothing waits for /me again.
 */
export function Providers({ children, initialMe = null }: { children: ReactNode; initialMe?: Me | null }) {
  const [client] = useState(() => {
    const created = makeQueryClient();
    if (initialMe) created.setQueryData(queryKeys.me(), initialMe);
    return created;
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
