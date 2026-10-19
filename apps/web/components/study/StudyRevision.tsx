"use client";

import { useState } from "react";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { SpokenText } from "@/components/SpokenPassage";
import type { StudyFeedback } from "@/lib/client/study";
import { studyRevisionCopy as copy } from "@/lib/copy/studyRevision";

export interface ReviewedDraft {
  text: string;
  feedback: StudyFeedback;
}

export interface RevisionReference {
  firstDraft: string;
  previous: ReviewedDraft;
}

/** Display only the server's grounded changes, without replacing the learner's draft. */
export function CorrectedDraft({
  reviewed,
  onAssisted,
}: {
  reviewed: ReviewedDraft;
  onAssisted: () => void;
}) {
  const [shown, setShown] = useState(false);
  const corrected = reviewed.feedback.corrected_text;
  if (!corrected || corrected === reviewed.text || !reviewed.feedback.corrections.length) return null;
  return (
    <div className="study-corrected-draft">
      <button
        type="button"
        className="study-text-button"
        aria-expanded={shown}
        onClick={() => {
          setShown(!shown);
          if (!shown) onAssisted();
        }}
      >
        <Icon name={shown ? "eye-off" : "lightbulb"} size={17} />
        <LearningText text={shown ? copy.hideSuggestion : copy.showSuggestion} />
      </button>
      {shown && (
        <div className="study-corrected-draft-text" data-testid="study-corrected-draft">
          <SpokenText text={{ nl: corrected }} />
          <p className="study-footnote">
            <LearningText text={copy.suggestionScope} />
          </p>
        </div>
      )}
    </div>
  );
}

/** A reference alongside the editor, never a current score for an edited answer. */
export function StudyRevision({
  reference,
  onAssisted,
}: {
  reference: RevisionReference;
  onAssisted: () => void;
}) {
  const { previous, firstDraft } = reference;
  return (
    <aside className="study-revision" aria-label={copy.previousFeedback.nl}>
      <div className="study-revision-heading">
        <h3>
          <LearningText text={copy.title} />
        </h3>
        <span className="study-revision-badge">
          <LearningText text={copy.aided} />
        </span>
      </div>
      <p className="study-revision-guidance">
        <LearningText text={copy.guidance} />
      </p>
      <p className="study-revision-previous-score">
        <LearningText text={previous.feedback.score === null ? copy.noPreviousScore : copy.previousScore} />
        {previous.feedback.score !== null && <strong>{previous.feedback.score}/10</strong>}
      </p>
      <p>
        <LearningText text={previous.feedback.summary} />
      </p>
      {previous.feedback.corrections.map((correction, index) => (
        <div className="study-correction" key={index}>
          <div>
            <del lang="nl">{correction.original}</del>
            <Icon name="arrow" size={16} />
            <strong lang="nl">{correction.replacement}</strong>
            <PhraseAudio text={correction.replacement} />
          </div>
          <p>
            <LearningText text={correction.explanation} />
          </p>
        </div>
      ))}
      <CorrectedDraft key={previous.feedback.corrected_text} reviewed={previous} onAssisted={onAssisted} />
      <details className="study-revision-draft">
        <summary>
          <LearningText text={copy.previousDraft} />
        </summary>
        <p lang="nl">{previous.text}</p>
      </details>
      {firstDraft !== previous.text && (
        <details className="study-revision-draft">
          <summary>
            <LearningText text={copy.firstDraft} />
          </summary>
          <p lang="nl">{firstDraft}</p>
        </details>
      )}
    </aside>
  );
}
