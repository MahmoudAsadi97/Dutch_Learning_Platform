"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LearningText } from "@/components/LanguageSupport";
import { UiText } from "@/components/ui/UiText";
import { apiJson } from "@/lib/client/api";
import type { LevelContract } from "@/lib/client/alignment";
import { alignmentCopy as copy } from "@/lib/copy/alignment";
import type { Skill } from "@/lib/types";

/** Targets are requested on demand; unavailable references never block existing practice. */
export function AlignmentPanel({ stageId, skill }: { stageId: string; skill: Skill }) {
  const [open, setOpen] = useState(false);
  const [contract, setContract] = useState<LevelContract | null>(null);
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    void apiJson<LevelContract>(`curriculum/${stageId}/alignment`, { signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted) setContract(value);
      })
      .catch((cause) => {
        if (cause?.name !== "AbortError") setFailed(true);
      });
    return () => controller.abort();
  }, [open, stageId, retry]);
  return (
    <details className="alignment-panel" onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary>
        <UiText text={copy.target} />
      </summary>
      {open &&
        (failed ? (
          <button
            className="linklike"
            onClick={() => {
              setFailed(false);
              setContract(null);
              setRetry((value) => value + 1);
            }}
          >
            <UiText text={copy.failed} />
          </button>
        ) : !contract || contract.id !== stageId ? (
          <p role="status">
            <UiText text={copy.loading} />
          </p>
        ) : (
          <div>
            <p className="eyebrow">
              <UiText text={contract.reference_status === "internal_bridge" ? copy.bridge : copy.reference} />
            </p>
            <p>
              <strong>
                <LearningText text={contract.skills[skill].target} />
              </strong>
            </p>
            <p className="small-text muted">
              <UiText text={copy.limits} tier="guide" />
            </p>
            <details>
              <summary>
                <UiText text={copy.sources} />
              </summary>
              <ul>
                {contract.source_details.map((source) => (
                  <li key={source.id}>
                    <a href={source.url} target="_blank" rel="noreferrer">
                      {source.title}
                    </a>
                  </li>
                ))}
              </ul>
            </details>
            <p>
              <Link href="/examens">
                <UiText text={copy.exams} />
              </Link>
            </p>
          </div>
        ))}
    </details>
  );
}
