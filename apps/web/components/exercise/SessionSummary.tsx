"use client";

import { useState, type Ref } from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import { errorCopy } from "@/lib/client/error-copy";
import type { Summary } from "@/lib/client/exercises";
import { words } from "@/lib/client/stories";
import { fill, uiCopy, type Copy } from "@/lib/ui-copy";

import { Dutch, Meaning } from "./ContentText";

type Suggestion = Summary["suggestions"][number];

/**
 * One suggested word and its save button. The button stays in place (focus stays on it) and says "Bewaard" once
 * saved; the status beside it is always there, so the change is announced.
 */
function SuggestionRow({ suggestion }: { suggestion: Suggestion }) {
  const [state, setState] = useState<"open" | "saving" | "saved">("open");
  const [error, setError] = useState<Copy | null>(null);
  async function save() {
    if (state !== "open") return;
    setState("saving");
    setError(null);
    try {
      await words.saveSuggestion(suggestion);
      setState("saved");
    } catch (cause) {
      setState("open");
      setError(errorCopy(cause, exerciseCopy.saveFailed));
    }
  }
  return (
    <li className="summary-word">
      <span className="summary-word-text">
        <Dutch text={suggestion.term} className="summary-term" />{" "}
        <Meaning text={{ en: suggestion.meaning_en, fa: suggestion.meaning_fa }} />
      </span>
      <Button
        variant="secondary"
        size="small"
        icon={state === "saved" ? "check" : "plus"}
        aria-disabled={state === "open" ? undefined : true}
        aria-label={state === "saved" ? undefined : fill(exerciseCopy.saveWord, { term: suggestion.term }).nl}
        onClick={() => void save()}
      >
        <UiText text={state === "saved" ? uiCopy.state.saved : uiCopy.action.save} inline />
      </Button>
      <span className="visually-hidden" role="status">
        {state === "saved" && <UiText text={uiCopy.state.saved} inline />}
      </span>
      {error && (
        <span className="summary-error" role="alert">
          <UiText text={error} tier="guide" />
        </span>
      )}
    </li>
  );
}

interface Props {
  summary: Summary;
  onAgain: () => void;
  headingRef?: Ref<HTMLHeadingElement>;
}

/** What the session did: answered, right first time, right on the second try, points; then what to keep. */
export function SessionSummary({ summary, onAgain, headingRef }: Props) {
  const stats: { label: Copy; value: number }[] = [
    { label: exerciseCopy.summaryFirstTry, value: summary.first_try_correct },
    { label: exerciseCopy.summaryFixed, value: summary.fixed_on_retry },
    { label: exerciseCopy.summaryPoints, value: summary.points_earned },
  ];
  // once per word, also for a summary stored before the server listed each word once
  const missed = [
    ...new Map(summary.missed.filter((entry) => entry.term).map((entry) => [entry.ref, entry])).values(),
  ];
  return (
    <section className="exercise-summary" aria-labelledby="summary-title">
      <h2 id="summary-title" className="exercise-question" tabIndex={-1} ref={headingRef}>
        <UiText text={exerciseCopy.summaryTitle} />
      </h2>
      <p className="exercise-lead">
        <UiText
          text={fill(exerciseCopy.summaryAnswered, {
            answered: summary.answered,
            total: summary.items_total,
          })}
          tier="guide"
        />
      </p>
      <dl className="summary-stats">
        {stats.map((stat) => (
          <div className="summary-stat" key={stat.label.nl}>
            <dt>
              <UiText text={stat.label} />
            </dt>
            <dd>{stat.value}</dd>
          </div>
        ))}
      </dl>
      {summary.session_bonus > 0 && (
        <p className="exercise-lead">
          <UiText text={fill(exerciseCopy.summaryBonus, { points: summary.session_bonus })} tier="guide" />
        </p>
      )}
      {missed.length > 0 && (
        <div className="summary-block">
          <h3>
            <UiText text={exerciseCopy.summaryMissed} />
          </h3>
          <ul className="summary-words">
            {missed.map((entry) => (
              <li key={entry.ref} className="summary-word">
                <Dutch text={entry.term} className="summary-term" />
              </li>
            ))}
          </ul>
        </div>
      )}
      {summary.suggestions.length > 0 && (
        <div className="summary-block">
          <h3>
            <UiText text={exerciseCopy.summarySuggest} />
          </h3>
          <p className="exercise-lead">
            <UiText text={exerciseCopy.summarySuggestLead} tier="guide" />
          </p>
          <ul className="summary-words">
            {summary.suggestions.map((suggestion) => (
              <SuggestionRow key={suggestion.key} suggestion={suggestion} />
            ))}
          </ul>
        </div>
      )}
      <div className="exercise-actions">
        <Button onClick={onAgain} icon="repeat">
          <UiText text={exerciseCopy.again} inline />
        </Button>
        <ButtonLink href="/" variant="secondary">
          <UiText text={exerciseCopy.backToday} inline />
        </ButtonLink>
      </div>
    </section>
  );
}
