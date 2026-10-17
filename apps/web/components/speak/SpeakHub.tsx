"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { StageLibraryPicker, useLibraryStages } from "@/components/LibraryStagePicker";
import { MissionCatalog } from "@/components/MissionCatalog";
import { UiText } from "@/components/ui/UiText";
import { apiJson } from "@/lib/client/api";
import { topicHref, type ConversationCatalog, type ConversationChoice } from "@/lib/client/learning-agents";
import { libraryHubsCopy as copy } from "@/lib/copy/libraryHubs";
import { isStageId, stageLabel } from "@/lib/domain/registry";
import { fill } from "@/lib/ui-copy";

/** Optional short partner conversations are distinct from the complete stage speaking banks. */
function ConversationStarters({ stageId }: { stageId: string }) {
  const [choices, setChoices] = useState<ConversationChoice[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<ConversationCatalog>("topic-conversations", { signal: controller.signal })
      .then((catalog) => {
        if (!controller.signal.aborted) setChoices(catalog.items);
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [attempt]);
  const items = choices?.filter((choice) => choice.stage_id === stageId) ?? [];
  return (
    <section className="speak-extra" aria-labelledby="speak-conversations-title">
      <h2 id="speak-conversations-title">
        <UiText text={copy.shortConversations} />
      </h2>
      <p className="muted">
        <UiText text={copy.conversationsNote} tier="guide" />
      </p>
      {failed ? (
        <p role="alert">
          <UiText text={copy.conversationsFailed} inline />{" "}
          <button
            type="button"
            className="linklike"
            onClick={() => {
              setFailed(false);
              setChoices(null);
              setAttempt((n) => n + 1);
            }}
          >
            <UiText text={copy.retry} inline />
          </button>
        </p>
      ) : choices === null ? (
        <p className="muted" role="status">
          <UiText text={copy.conversationsLoading} />
        </p>
      ) : items.length === 0 ? (
        <p className="muted">
          <UiText text={copy.conversationsEmpty} tier="guide" />
        </p>
      ) : (
        <ul className="speak-choices">
          {items.map((choice) => {
            const href = topicHref(choice.stage_id, "speaking", choice.topic_id);
            return href ? (
              <li key={choice.id}>
                <Link className="button secondary small" href={href}>
                  <Icon name="message" size={16} />
                  <LearningText text={choice.title} />
                </Link>
              </li>
            ) : null;
          })}
        </ul>
      )}
    </section>
  );
}

/** Speaking starts with all twelve stage banks; the microphone studio is a compact utility. */
export function SpeakHub() {
  const params = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const requested = params.get("stage") ?? "pre-a1";
  const stageId = isStageId(requested) ? requested : "pre-a1";
  const { stages, failed, retry } = useLibraryStages();
  const coverage = stages?.find((stage) => stage.id === stageId)?.coverage;
  return (
    <div className="speak-hub" data-testid="speaking-hub">
      <header className="page-heading">
        <div>
          <h1>
            <UiText text={copy.speakingTitle} />
          </h1>
          <p>
            <UiText text={copy.speakingIntro} tier="guide" />
          </p>
        </div>
      </header>
      <StageLibraryPicker
        stageId={stageId}
        onChange={(stage) => router.replace(`${pathname}?stage=${stage}`, { scroll: false })}
      />
      {failed ? (
        <p className="error" role="alert">
          <UiText text={copy.failed} inline />{" "}
          <button className="linklike" onClick={retry}>
            <UiText text={copy.retry} inline />
          </button>
        </p>
      ) : !stages ? (
        <p role="status">
          <UiText text={copy.loading} />
        </p>
      ) : null}
      <section className="card speak-main" aria-labelledby="speak-stage-title">
        <div>
          <span className="quiet-badge">{stageLabel(stageId)}</span>
          <h2 id="speak-stage-title">
            <UiText text={copy.speakingOpen} />
          </h2>
          {coverage && (
            <p className="speak-topic-count">
              <UiText text={fill(copy.speakingTopics, { count: coverage.skill_topics.speaking })} />
            </p>
          )}
          <p className="muted">
            <UiText text={copy.speakingLoop} tier="guide" />
          </p>
        </div>
        <Link className="button" href={`/learn/${stageId}?skill=speaking`}>
          <Icon name="mic" size={18} />
          <UiText text={copy.speakingOpen} inline />
          <Icon name="arrow" size={18} />
        </Link>
      </section>
      <ConversationStarters stageId={stageId} />
      <MissionCatalog />
      <aside className="speak-microphone" aria-labelledby="speak-studio-title">
        <Icon name="mic" size={24} />
        <div>
          <h2 id="speak-studio-title">
            <UiText text={copy.studioTitle} />
          </h2>
          <p className="small-text muted">
            <UiText text={copy.studioNote} tier="guide" />
          </p>
        </div>
        <Link className="linklike" href="/speech-check">
          <UiText text={copy.studioOpen} inline /> <Icon name="arrow" size={16} />
        </Link>
      </aside>
    </div>
  );
}
