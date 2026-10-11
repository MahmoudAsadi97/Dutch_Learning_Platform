"use client";

import { useState, type ReactNode, type Ref } from "react";

import { Icon } from "@/components/Icon";
import { Button, ButtonLink } from "@/components/ui/Button";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import { errorCopy } from "@/lib/client/error-copy";
import type { Summary } from "@/lib/client/exercises";
import { words } from "@/lib/client/stories";
import { fill, uiCopy, type Copy } from "@/lib/ui-copy";

import { againLabel, completionLines, completionState, summaryActions } from "./completion";
import { Dutch, Meaning } from "./ContentText";
import { ItemHeading } from "./heading";

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

/** A host page's own way out (a practice topic's), in place of the link back to Today. */
export interface SessionExit {
  label: Copy;
  onExit: () => void;
}

interface Props {
  summary: Summary;
  onAgain: () => void;
  /** A topic's short session on the questions missed the first time (offered when there are some). */
  onRetry?: () => void;
  exit?: SessionExit;
  headingRef?: Ref<HTMLHeadingElement>;
  /** Shown after the numbers: a topic's passage, read again. */
  children?: ReactNode;
}

/**
 * What the session did: answered, right first time, right on the second try, points; for a topic, what it did
 * for the topic (the server decides; never in a miss colour); then what to keep, and the ways on.
 */
export function SessionSummary({ summary, onAgain, onRetry, exit, headingRef, children }: Props) {
  const completion = summary.completion ?? null;
  const lines = completionLines(completion);
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
      <ItemHeading id="summary-title" className="exercise-question" tabIndex={-1} ref={headingRef}>
        <UiText text={exerciseCopy.summaryTitle} />
      </ItemHeading>
      <p className="exercise-lead">
        <UiText
          text={fill(exerciseCopy.summaryAnswered, {
            answered: summary.answered,
            total: summary.items_total,
          })}
          tier="guide"
        />
      </p>
      {completion && lines.length > 0 && (
        <div className="summary-completion" data-state={completionState(completion)}>
          <Icon name={completionState(completion) === "done" ? "check" : "info"} size={20} />
          <div>
            {lines.map((line) => (
              <p key={line.key}>
                <UiText
                  text={line.values ? fill(exerciseCopy[line.key], line.values) : exerciseCopy[line.key]}
                  tier="guide"
                />
              </p>
            ))}
          </div>
        </div>
      )}
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
      {children}
      {missed.length > 0 && (
        <div className="summary-block">
          <ItemHeading sub className="summary-subtitle">
            <UiText text={exerciseCopy.summaryMissed} />
          </ItemHeading>
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
          <ItemHeading sub className="summary-subtitle">
            <UiText text={exerciseCopy.summarySuggest} />
          </ItemHeading>
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
        {summaryActions(completion, onRetry !== undefined).map(({ kind, variant }) => {
          if (kind === "retry" && onRetry)
            return (
              <Button key={kind} variant={variant} onClick={onRetry} icon="repeat">
                <UiText text={exerciseCopy.retryMissed} inline />
              </Button>
            );
          if (kind === "again")
            return (
              <Button key={kind} variant={variant} onClick={onAgain} icon="repeat">
                <UiText text={exerciseCopy[againLabel(completion)]} inline />
              </Button>
            );
          return exit ? (
            <Button key={kind} variant={variant} onClick={exit.onExit} icon="arrow" iconEnd>
              <UiText text={exit.label} inline />
            </Button>
          ) : (
            <ButtonLink key={kind} href="/" variant={variant}>
              <UiText text={exerciseCopy.backToday} inline />
            </ButtonLink>
          );
        })}
      </div>
    </section>
  );
}
