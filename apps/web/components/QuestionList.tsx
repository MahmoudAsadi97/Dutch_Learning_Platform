"use client";

import { useState } from "react";

import { HelpLadder } from "@/components/HelpLadder";
import type { HelpRung, Question, StepProgress } from "@/lib/types";

interface Props {
  stepKey: string;
  questions: Question[];
  progress: StepProgress | undefined;
  /** Sends one answer to the server, which decides whether it is correct. Rejects when it could not be recorded. */
  onAnswer: (questionId: string, chosenIndex: number) => Promise<{ correct: boolean; answer_index: number }>;
  onHelp: (rung: HelpRung, questionId: string) => Promise<void>;
}

type Verdict = { correct: boolean; answer_index: number };

/**
 * Multiple-choice questions of a reading or listening step. The browser only collects the choices;
 * "Controleer" sends them to the API, which judges them against the mission document and stores the
 * answers as evidence. The verdicts shown come from the server.
 */
export function QuestionList({ stepKey, questions, progress, onAnswer, onHelp }: Props) {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [verdicts, setVerdicts] = useState<Record<string, Verdict>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const answered = progress?.answered ?? {};
  const allChosen = questions.every((q) => answers[q.id] !== undefined);
  const correct = Object.values(verdicts).filter((v) => v.correct).length;
  const checked = Object.keys(verdicts).length === questions.length && questions.length > 0;

  async function check() {
    setBusy(true);
    setError("");
    try {
      const next: Record<string, Verdict> = {};
      for (const question of questions) {
        const chosen = answers[question.id];
        if (chosen === undefined) continue;
        next[question.id] = await onAnswer(question.id, chosen);
      }
      setVerdicts(next);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Antwoorden konden niet worden opgeslagen.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card" aria-labelledby={`${stepKey}-questions-heading`}>
      <h3 id={`${stepKey}-questions-heading`}>Vragen</h3>
      {questions.map((question, qIndex) => {
        const verdict = verdicts[question.id];
        return (
          <div className="question" key={question.id}>
            <fieldset disabled={busy}>
              <legend>
                <span lang="nl">
                  {qIndex + 1}. {question.prompt.nl}
                </span>
                <span className="fa" lang="fa" style={{ display: "block" }}>
                  {question.prompt.fa}
                </span>
              </legend>
              {question.options.map((option, index) => {
                const id = `${stepKey}-${question.id}-${index}`;
                return (
                  <label key={id} htmlFor={id}>
                    <input
                      id={id}
                      type="radio"
                      name={`${stepKey}-${question.id}`}
                      value={index}
                      checked={answers[question.id] === index}
                      onChange={() => {
                        setVerdicts((current) => {
                          const rest = { ...current };
                          delete rest[question.id];
                          return rest;
                        });
                        setAnswers({ ...answers, [question.id]: index });
                      }}
                    />
                    <span>
                      <span lang="nl">{option.nl}</span>
                      <span className="fa muted" lang="fa" style={{ display: "block", fontSize: "0.9rem" }}>
                        {option.fa}
                      </span>
                    </span>
                  </label>
                );
              })}
              {verdict && (
                <p role="status" data-testid={`result-${question.id}`}>
                  {verdict.correct ? <span className="label ok">Juist</span> : <span className="label bad">Nog niet juist</span>}
                </p>
              )}
              {!verdict && answered[question.id] !== undefined && (
                <p className="muted" style={{ fontSize: "0.85rem" }} data-testid={`earlier-${question.id}`}>
                  Eerder beantwoord{answered[question.id] ? " (juist)" : ""}.
                </p>
              )}
              {question.help.length > 0 && (
                <HelpLadder rungs={question.help} idPrefix={`${stepKey}-${question.id}`} onReveal={(rung) => onHelp(rung, question.id)} />
              )}
            </fieldset>
          </div>
        );
      })}
      <div className="status-line">
        <button type="button" className="button" onClick={() => void check()} disabled={!allChosen || busy} data-testid={`${stepKey}-check`}>
          {busy ? "Bezig…" : "Controleer"} · <span className="fa" lang="fa" style={{ display: "inline" }}>بررسی</span>
        </button>
        {checked && (
          <span data-testid="score" aria-live="polite">
            {correct} van {questions.length} juist
          </span>
        )}
        {progress?.completed && (
          <span className="label ok" data-testid={`${stepKey}-done`}>
            stap voltooid
          </span>
        )}
        {error && (
          <span className="error" role="alert">
            {error}
          </span>
        )}
      </div>
    </section>
  );
}
