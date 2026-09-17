"use client";

import { useState } from "react";

import { ContentLabel } from "@/components/ContentLabel";
import { HelpLadder } from "@/components/HelpLadder";
import type { ReadingPayload, Step } from "@/lib/types";

interface Props {
  step: Step & { payload: ReadingPayload };
  labels: { unreviewed_nl: string; unreviewed_fa: string };
}

/**
 * Renders the reading step: the fixed Dutch text with its review label, a toggle for the
 * Persian rendering, vocabulary, the comprehension questions and the help ladder.
 * Answers are checked in the browser only; recording them as evidence is M2 work.
 */
export function ReadingStep({ step, labels }: Props) {
  const { payload } = step;
  const [showPersian, setShowPersian] = useState(false);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [checked, setChecked] = useState(false);

  const correct = payload.questions.filter((q) => answers[q.id] === q.answer_index).length;

  return (
    <article aria-labelledby="step-title" data-step={step.key}>
      <header>
        <h2 id="step-title">
          {step.title.nl}
          <span className="fa" lang="fa" style={{ display: "block", fontSize: "1rem", fontWeight: 400 }}>
            {step.title.fa}
          </span>
        </h2>
        <p>
          <ContentLabel status={step.instructions.review_status} labelNl={labels.unreviewed_nl} labelFa={labels.unreviewed_fa} />
        </p>
        <p lang="nl">{step.instructions.nl}</p>
        <p className="fa" lang="fa">
          {step.instructions.fa}
        </p>
      </header>

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

      <section className="card" aria-labelledby="questions-heading">
        <h3 id="questions-heading">Vragen</h3>
        {payload.questions.map((question, qIndex) => (
          <div className="question" key={question.id}>
            <fieldset>
              <legend>
                <span lang="nl">
                  {qIndex + 1}. {question.prompt.nl}
                </span>
                <span className="fa" lang="fa" style={{ display: "block" }}>
                  {question.prompt.fa}
                </span>
              </legend>
              {question.options.map((option, index) => {
                const id = `${question.id}-${index}`;
                const isChosen = answers[question.id] === index;
                return (
                  <label key={id} htmlFor={id}>
                    <input
                      id={id}
                      type="radio"
                      name={question.id}
                      value={index}
                      checked={isChosen}
                      onChange={() => {
                        setChecked(false);
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
              {checked && answers[question.id] !== undefined && (
                <p role="status" data-testid={`result-${question.id}`}>
                  {answers[question.id] === question.answer_index ? (
                    <span className="label ok">Juist</span>
                  ) : (
                    <span className="label bad">Nog niet juist</span>
                  )}
                </p>
              )}
              {question.help.length > 0 && <HelpLadder rungs={question.help} idPrefix={question.id} />}
            </fieldset>
          </div>
        ))}
        <div className="status-line">
          <button
            type="button"
            className="button"
            onClick={() => setChecked(true)}
            disabled={Object.keys(answers).length < payload.questions.length}
          >
            Controleer · <span className="fa" lang="fa" style={{ display: "inline" }}>بررسی</span>
          </button>
          {checked && (
            <span data-testid="score" aria-live="polite">
              {correct} van {payload.questions.length} juist
            </span>
          )}
          <span className="muted">Antwoorden worden in deze release nog niet als bewijs opgeslagen (M2).</span>
        </div>
      </section>

      <section className="card" aria-labelledby="help-heading">
        <h3 id="help-heading">
          Hulp · <span className="fa" lang="fa" style={{ display: "inline" }}>کمک</span>
        </h3>
        <HelpLadder rungs={payload.help} idPrefix={step.key} />
      </section>
    </article>
  );
}
