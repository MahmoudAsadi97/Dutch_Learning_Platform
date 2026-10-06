"use client";

import { useQuery } from "@tanstack/react-query";
import { apiJson } from "../api";
import { queryKeys } from "../query-keys";

export interface UsageCounter {
  used: number;
  reserved: number;
  limit: number;
  remaining: number;
}

export interface Usage {
  period: string;
  counters: Record<string, { daily: UsageCounter; total: UsageCounter }>;
  pricing_table_entries: number;
  estimated_cost: { currency?: string; amount?: number } | null;
  note: string;
}

export function fetchUsage(signal?: AbortSignal): Promise<Usage> {
  return apiJson<Usage>("usage", { signal });
}

/** The learner's allowance counters; invalidate `queryKeys.usage()` after any paid action. */
export function useUsage() {
  return useQuery({ queryKey: queryKeys.usage(), queryFn: ({ signal }) => fetchUsage(signal) });
}
