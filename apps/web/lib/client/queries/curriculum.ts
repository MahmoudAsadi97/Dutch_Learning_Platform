"use client";

import { useQuery } from "@tanstack/react-query";
import { apiJson } from "../api";
import type { CurriculumCatalog } from "../curriculum";
import { queryKeys } from "../query-keys";

/**
 * GET /curriculum, shared by the path, the progress page, the final check and the review queue: one
 * request per 30 s for all of them. The payload is typed as the catalogue; a caller that reads extra
 * fields (the progress page's latest checks) narrows it with the type parameter.
 */
export function useCurriculumCatalog<T extends CurriculumCatalog = CurriculumCatalog>() {
  return useQuery({
    queryKey: queryKeys.curriculum.catalog(),
    queryFn: ({ signal }) => apiJson<T>("curriculum", { signal }),
  });
}
