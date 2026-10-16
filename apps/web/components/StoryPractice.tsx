"use client";

import Link from "next/link";
import { useState } from "react";
import { LearningText } from "@/components/LanguageSupport";
import { WritingCoach } from "@/components/WritingCoach";
import { storyLearningCopy } from "@/lib/copy/storyLearning";
import { storageKeys } from "@/lib/client/storage";

type Props = { stageId: string; topicId?: string; storyId?: string; learnerKey?: string };

export function StoryPractice(props: Props) {
  return <StoryPracticeSession key={`${props.learnerKey}.${props.stageId}.${props.storyId}`} {...props} />;
}

function StoryPracticeSession({ stageId, topicId, storyId, learnerKey }: Props) {
  const storageKey =
    learnerKey && storyId ? storageKeys.topicDraft(learnerKey, stageId, "story", storyId) : null;
  const [initial] = useState(() => {
    try {
      return {
        text: storageKey ? (sessionStorage.getItem(storageKey) ?? "").slice(0, 5000) : "",
        failed: false,
      };
    } catch {
      return { text: "", failed: true };
    }
  });
  const [draft, setDraft] = useState(initial.text);
  const [storageFailed, setStorageFailed] = useState(initial.failed);
  function updateDraft(text: string) {
    setDraft(text);
    if (!storageKey) return;
    try {
      sessionStorage.setItem(storageKey, text);
      setStorageFailed(false);
    } catch {
      setStorageFailed(true);
    }
  }
  const prompt = storyLearningCopy[stageId as keyof typeof storyLearningCopy] ?? storyLearningCopy.a1;
  return (
    <section className="story-transfer" aria-labelledby="story-transfer-title">
      <p className="eyebrow">
        <LearningText text={storyLearningCopy.eyebrow} />
      </p>
      <h4 id="story-transfer-title">
        <LearningText text={storyLearningCopy.title} />
      </h4>
      <p>
        <LearningText text={prompt} />
      </p>
      <label htmlFor="story-response">
        <LearningText text={storyLearningCopy.responseLabel} />
      </label>
      <textarea
        id="story-response"
        lang="nl"
        rows={4}
        maxLength={5000}
        value={draft}
        onChange={(event) => updateDraft(event.target.value)}
      />
      <p className="small-text muted">
        <LearningText
          text={
            storageKey
              ? storageFailed
                ? storyLearningCopy.draftSaveFailed
                : storyLearningCopy.draftSaved
              : storyLearningCopy.scratchNote
          }
        />
      </p>
      {draft.trim() && <WritingCoach stageId={stageId} text={draft} onApply={updateDraft} />}
      {topicId && (
        <div className="story-skill-links" aria-label={storyLearningCopy.skillLinks.nl}>
          {(["reading", "listening", "speaking", "writing"] as const).map((skill) => (
            <Link
              className="button secondary"
              key={skill}
              href={`/learn/${stageId}?skill=${skill}&topic=${encodeURIComponent(topicId)}`}
            >
              <LearningText
                text={
                  {
                    reading: storyLearningCopy.reading,
                    listening: storyLearningCopy.listening,
                    speaking: storyLearningCopy.speaking,
                    writing: storyLearningCopy.writing,
                  }[skill]
                }
              />
            </Link>
          ))}
        </div>
      )}
      <p className="story-revisit">
        <LearningText text={storyLearningCopy.revisit} />
      </p>
    </section>
  );
}
