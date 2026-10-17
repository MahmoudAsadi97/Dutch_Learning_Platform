"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { UiText } from "@/components/ui/UiText";
import { apiJson } from "@/lib/client/api";
import type { CurriculumCatalog, StageSummary } from "@/lib/client/curriculum";
import { isStageId, STAGE_IDS, stageLabel, type StageId } from "@/lib/domain/registry";
import { libraryHubsCopy as copy } from "@/lib/copy/libraryHubs";

/** One catalogue request feeds the level chooser and its counts; a failed request never invents totals. */
export function useLibraryStages() {
  const [stages, setStages] = useState<StageSummary[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<CurriculumCatalog>("curriculum", { signal: controller.signal })
      .then((catalog) => {
        if (!controller.signal.aborted) {
          setStages(catalog.stages);
          setFailed(false);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [attempt]);
  return {
    stages,
    failed,
    retry: () => {
      setFailed(false);
      setAttempt((value) => value + 1);
    },
  };
}

export function StageLibraryPicker({
  stageId,
  onChange,
}: {
  stageId: StageId;
  onChange: (stage: StageId) => void;
}) {
  return (
    <div className="library-hub-level">
      <label htmlFor="library-hub-stage">
        <UiText text={copy.level} />
      </label>
      <select
        id="library-hub-stage"
        value={stageId}
        onChange={(event) => {
          if (isStageId(event.target.value)) onChange(event.target.value);
        }}
      >
        {STAGE_IDS.map((id) => (
          <option key={id} value={id}>
            {stageLabel(id)}
          </option>
        ))}
      </select>
      <Link className="linklike" href={`/learn/${stageId}`}>
        <UiText text={copy.openLevel} inline /> <Icon name="arrow" size={16} />
      </Link>
    </div>
  );
}
