"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { LearningText } from "@/components/LanguageSupport";
import { TopicConversation } from "@/components/TopicConversation";
import { TopicReader } from "@/components/SkillTopicPractice";
import { apiJson } from "@/lib/client/api";
import { friendlyError, type CurriculumStage } from "@/lib/client/curriculum";
import type { ConversationCatalog } from "@/lib/client/learning-agents";
import { useNavigationCheck, useNavigationGuard } from "@/lib/client/navigation";
import { studyHref } from "@/lib/client/study";
import type { Skill } from "@/lib/domain/registry";
import { studyCopy } from "@/lib/copy/study";
import { StudyError } from "./StudyShared";

/** Optional durable exercises stay inside the level, apart from temporary guided practice. */
export function StudyDeepPractice({
  stageId,
  skill,
  topicId,
  conversation,
}: {
  stageId: string;
  skill: Skill;
  topicId?: string;
  conversation: boolean;
}) {
  const router = useRouter();
  const canLeave = useNavigationCheck();
  const registerGuard = useNavigationGuard();
  const [stage, setStage] = useState<CurriculumStage | null>(null);
  const [catalog, setCatalog] = useState<ConversationCatalog | null>(null);
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const activityChanged = useCallback((value: boolean) => {
    setBusy(value);
    if (!value) setError((current) => (current === studyCopy.waitBeforeLeaving.nl ? "" : current));
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      apiJson<CurriculumStage>(`curriculum/${stageId}`, { signal: controller.signal }),
      conversation
        ? apiJson<ConversationCatalog>(`topic-conversations?stage_id=${stageId}`, {
            signal: controller.signal,
          })
        : Promise.resolve(null),
    ])
      .then(([nextStage, nextCatalog]) => {
        if (controller.signal.aborted) return;
        setStage(nextStage);
        setCatalog(nextCatalog);
        setError("");
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(friendlyError(cause, "load"));
      });
    return () => controller.abort();
  }, [stageId, conversation, retry]);
  useEffect(() => {
    if (!busy) return;
    registerGuard(async () => {
      setError(studyCopy.waitBeforeLeaving.nl);
      return false;
    });
    return () => registerGuard(null);
  }, [busy, registerGuard]);
  async function choose(topic: string) {
    if (await canLeave()) router.push(studyHref(stageId, "speaking", { topic, view: "conversation" }));
  }
  const choices =
    catalog?.learner_key === stage?.learner_key
      ? (catalog?.items.filter((item) => item.stage_id === stageId) ?? [])
      : [];
  const current = choices.find((item) => item.topic_id === topicId);
  return (
    <section className="study-deep-practice" data-testid="study-deep-practice">
      <Link className="study-text-button" href={studyHref(stageId, skill)}>
        <LearningText text={studyCopy.backToTopicPractice} />
      </Link>
      <header className="study-page-heading">
        <h1>
          <LearningText text={conversation ? studyCopy.situationConversations : studyCopy.extendedPractice} />
        </h1>
        <p>
          <LearningText
            text={conversation ? studyCopy.savedConversationNotice : studyCopy.savedPracticeNotice}
          />
        </p>
      </header>
      {error && (
        <StudyError message={error} retry={busy ? undefined : () => setRetry((value) => value + 1)} />
      )}
      {!stage ? (
        !error && (
          <p role="status">
            <LearningText text={studyCopy.loadingLesson} />
          </p>
        )
      ) : conversation ? (
        <>
          {!open && (
            <div className="conversation-topic-choices">
              <p>
                <LearningText
                  text={choices.length ? studyCopy.chooseConversation : studyCopy.noConversations}
                />
              </p>
              <div>
                {choices.map((choice) => (
                  <button
                    className="button secondary"
                    key={choice.id}
                    disabled={busy}
                    aria-pressed={choice.topic_id === topicId}
                    onClick={() => void choose(choice.topic_id)}
                  >
                    <LearningText text={choice.title} />
                  </button>
                ))}
              </div>
            </div>
          )}
          {current && (
            <TopicConversation
              stageId={stageId}
              topicId={current.topic_id}
              learnerKey={stage.learner_key}
              onActivityChange={activityChanged}
              onOpenChange={setOpen}
            />
          )}
        </>
      ) : topicId ? (
        <TopicReader
          stageId={stageId}
          skill={skill}
          learnerKey={stage.learner_key}
          topicId={topicId}
          maxSeconds={stage.policy?.recording_max_seconds}
          entry="task"
          onActivityChange={activityChanged}
          onCompleted={() => {}}
          onBack={() => router.push(studyHref(stageId, skill))}
        />
      ) : null}
    </section>
  );
}
