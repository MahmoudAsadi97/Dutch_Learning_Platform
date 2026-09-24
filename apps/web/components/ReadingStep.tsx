"use client";

import { useState } from "react";

import { LearningText, useLanguageSupport } from "@/components/LanguageSupport";
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
  registerBeforeLeave?: (guard: (() => Promise<boolean>) | null) => void;
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
  const { showEnglish, showPersian: supportPersian } = useLanguageSupport();
  const [showPersian, setShowPersian] = useState(false);
  const [translationBusy, setTranslationBusy] = useState(false);
  const [translationError, setTranslationError] = useState("");
  const progress = detail?.session.step_progress[step.key];

  async function answer(questionId: string, chosenIndex: number) {
    const current = detail ?? (await ensureSession());
    const result = await submitAnswer(current, step.key, questionId, chosenIndex);
    onDetail(result.detail);
    onProgressChanged();
    return { correct: result.correct, answer_index: result.answer_index };
  }

  async function help(rung: HelpRung, questionId = "") {
    const current = detail ?? (await ensureSession());
    onDetail(await recordHelp(current, step.key, rung, questionId));
  }

  async function toggleTranslation() {
    if (showPersian) { setShowPersian(false); return; }
    setTranslationBusy(true);
    setTranslationError("");
    try {
      const current = detail ?? (await ensureSession());
      onDetail(await recordHelp(current, step.key, { level: 3, kind: "reading_translation" }));
      setShowPersian(true);
    } catch {
      setTranslationError("De vertaling is nog niet getoond: hulp kon niet worden opgeslagen. Probeer opnieuw.");
    } finally {
      setTranslationBusy(false);
    }
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
            disabled={translationBusy}
            onClick={() => void toggleTranslation()}
          >
            <LearningText text={{nl: showPersian ? "Verberg de vertaling" : "Toon de vertaling", en: showPersian ? "Hide translation" : "Show translation", fa: showPersian ? "پنهان کردن ترجمه" : "نمایش ترجمه"}} />
          </button>
        </p>
        {translationError && <p className="error" role="alert">{translationError}</p>}
        {showPersian && (
          <div id="reading-text-fa" className="dutch-text" data-testid="reading-translation">
            {showEnglish && payload.text.en && <p lang="en">{payload.text.en}</p>}
            {supportPersian && <p lang="fa" dir="rtl" className="fa" data-testid="reading-text-fa">{payload.text.fa}</p>}
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
                <th scope="col">Betekenis</th>
                <th scope="col">Opmerking</th>
              </tr>
            </thead>
            <tbody>
              {payload.vocabulary.map((item) => (
                <tr key={item.nl}>
                  <td lang="nl">{item.nl}</td>
                  <td><LearningText text={item} supportOnly /></td>
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
          <LearningText text={{nl: "Hulp", en: "Help", fa: "کمک"}} />
        </h3>
        <HelpLadder rungs={payload.help} idPrefix={step.key} onReveal={(rung) => help(rung)} />
      </section>

      <FeedbackPanel stepKey={step.key} detail={detail} onDetail={onDetail} onProgressChanged={onProgressChanged} />
    </article>
  );
}
