"use client";

import { useState } from "react";

import { ContentLabel } from "@/components/ContentLabel";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { HelpLadder } from "@/components/HelpLadder";
import { QuestionList } from "@/components/QuestionList";
import { StepHeader } from "@/components/StepHeader";
import { recordHelp, submitAnswer } from "@/lib/client/practice";
import type { HelpRung, ReadingPayload, SessionDetail, Step } from "@/lib/types";

export interface StepProps {
  labels: { unreviewed_nl: string; unreviewed_fa: string };
  detail: SessionDetail | null;
  /** Resolves the active session of this variant, starting one when needed. */
  ensureSession: () => Promise<SessionDetail>;
  onDetail: (detail: SessionDetail) => void;
  onProgressChanged: () => void;
}

interface Props extends StepProps {
  step: Step & { payload: ReadingPayload };
}

/**
 * The reading step: the fixed Dutch text with its review label, a toggle for the Persian rendering,
 * vocabulary, the comprehension questions (judged by the API and stored as evidence) and the help ladder
 * (every rung opened is stored as help-usage evidence).
 */
export function ReadingStep({ step, labels, detail, ensureSession, onDetail, onProgressChanged }: Props) {
  const { payload } = step;
  const [showPersian, setShowPersian] = useState(false);
  const progress = detail?.session.step_progress[step.key];

  async function answer(questionId: string, chosenIndex: number) {
    const current = detail ?? (await ensureSession());
    const result = await submitAnswer(current, step.key, questionId, chosenIndex);
    onDetail(result.detail);
    onProgressChanged();
    return { correct: result.correct, answer_index: result.answer_index };
  }

  function help(rung: HelpRung, questionId = "") {
    void (async () => {
      try {
        const current = detail ?? (await ensureSession());
        onDetail(await recordHelp(current, step.key, rung, questionId));
      } catch {
        // the rung is shown regardless; the evidence is best effort
      }
    })();
  }

  return (
    <article aria-labelledby="step-title" data-step={step.key} data-step-type="reading">
      <StepHeader step={step} labels={labels} />

      <section className="card" aria-labelledby="reading-text-heading">
        <h3 id="reading-text-heading">Tekst</h3>
        <p>
          <ContentLabel status={payload.text.review_status} labelNl={labels.unreviewed_nl} labelFa={labels.unreviewed_fa} />
        </p>
        <div className="dutch-text nl" lang="nl" data-testid="reading-text">
          {payload.text.nl}
        </div>
        <p style={{ marginTop: "0.75rem" }}>
          <button
            type="button"
            className="button secondary"
            aria-expanded={showPersian}
            aria-controls="reading-text-fa"
            onClick={() => setShowPersian(!showPersian)}
          >
            {showPersian ? "Verberg de Perzische vertaling" : "Toon de Perzische vertaling"} ·{" "}
            <span className="fa" lang="fa" style={{ display: "inline" }}>
              {showPersian ? "پنهان کردن ترجمه" : "نمایش ترجمهٔ فارسی"}
            </span>
          </button>
        </p>
        {showPersian && (
          <div id="reading-text-fa" className="dutch-text fa" lang="fa" dir="rtl" data-testid="reading-text-fa">
            {payload.text.fa}
          </div>
        )}
      </section>

      {payload.vocabulary.length > 0 && (
        <section className="card" aria-labelledby="vocab-heading">
          <h3 id="vocab-heading">Woordenschat</h3>
          <table className="plain">
            <thead>
              <tr>
                <th scope="col">Nederlands</th>
                <th scope="col" className="fa" lang="fa">
                  فارسی
                </th>
                <th scope="col">Opmerking</th>
              </tr>
            </thead>
            <tbody>
              {payload.vocabulary.map((item) => (
                <tr key={item.nl}>
                  <td lang="nl">{item.nl}</td>
                  <td className="fa" lang="fa">
                    {item.fa}
                  </td>
                  <td className="muted" lang="nl">
                    {item.note_nl}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <QuestionList stepKey={step.key} questions={payload.questions} progress={progress} onAnswer={answer} onHelp={help} />

      <section className="card" aria-labelledby="help-heading">
        <h3 id="help-heading">
          Hulp · <span className="fa" lang="fa" style={{ display: "inline" }}>کمک</span>
        </h3>
        <HelpLadder rungs={payload.help} idPrefix={step.key} onReveal={(rung) => help(rung)} />
      </section>

      <FeedbackPanel stepKey={step.key} detail={detail} onDetail={onDetail} onProgressChanged={onProgressChanged} />
    </article>
  );
}
