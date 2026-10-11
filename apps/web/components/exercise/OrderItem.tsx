"use client";

import { useEffect, useId, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import { useLanguageSupport } from "@/components/LanguageSupport";
import { fill } from "@/lib/ui-copy";

import type { BoardProps } from "./boardProps";
import { Dutch } from "./ContentText";

/**
 * Putting the sentences of a paragraph back in order: each sentence moves up or down with its own buttons (no
 * dragging), and focus stays on the button that moved it. Every order is a whole answer. Answered, it shows the
 * right order with the translation, and marks the sentences that stood elsewhere.
 */
export function OrderItem({ prompt, feedback, onDraft, headingRef }: BoardProps<"sentence_order">) {
  const headingId = useId();
  const { showEnglish, showPersian } = useLanguageSupport();
  const [order, setOrder] = useState<string[]>(() => prompt.sentences.map((sentence) => sentence.id));
  const textOf = new Map(prompt.sentences.map((sentence) => [sentence.id, sentence.nl ?? ""]));
  const list = useRef<HTMLOListElement>(null);
  const keep = useRef<string | null>(null);

  // every order is an answer: the board can be checked as it is
  useEffect(() => {
    onDraft({ order });
  }, [order, onDraft]);

  // a moved sentence keeps the focus on the button that moved it, or on its other button at the list's edge
  useEffect(() => {
    if (!keep.current) return;
    const wanted = list.current?.querySelector<HTMLButtonElement>(
      `button[data-move="${keep.current}"]:not(:disabled)`,
    );
    const other = list.current?.querySelector<HTMLButtonElement>(
      `button[data-moving="${keep.current.split(":")[0]}"]:not(:disabled)`,
    );
    (wanted ?? other)?.focus();
    keep.current = null;
  }, [order]);

  function move(id: string, by: -1 | 1) {
    const from = order.indexOf(id);
    const to = from + by;
    if (to < 0 || to >= order.length) return;
    const next = [...order];
    [next[from], next[to]] = [next[to], next[from]];
    keep.current = `${id}:${by}`;
    setOrder(next);
  }

  if (feedback) {
    const right = feedback.order ?? [];
    const given = feedback.given_order ?? order;
    const translation = feedback.translation ?? {};
    const language = showEnglish && translation.en ? "en" : showPersian && translation.fa ? "fa" : null;
    return (
      <div className="exercise-item">
        <h2 className="exercise-question" id={headingId} tabIndex={-1} ref={headingRef}>
          <UiText text={exerciseCopy.rightOrder} tier="guide" />
        </h2>
        <ol className="order-list">
          {right.map((id, index) => (
            <li key={id} className="order-row" data-state={given[index] === id ? "correct" : "incorrect"}>
              <Dutch text={textOf.get(id)} className="order-text" />
              {language && (
                <span
                  lang={language}
                  dir={language === "fa" ? "rtl" : undefined}
                  className="order-translation"
                >
                  {translation[language][index]}
                </span>
              )}
            </li>
          ))}
        </ol>
      </div>
    );
  }

  return (
    <div className="exercise-item">
      <h2 className="exercise-question" id={headingId} tabIndex={-1} ref={headingRef}>
        <UiText text={exerciseCopy.askOrder} tier="guide" />
      </h2>
      <ol className="order-list" ref={list} aria-labelledby={headingId}>
        {order.map((id, index) => (
          <li key={id} className="order-row">
            <span className="order-number" aria-hidden="true">
              {index + 1}
            </span>
            <Dutch text={textOf.get(id)} className="order-text" />
            <span className="order-moves">
              <Button
                variant="ghost"
                size="small"
                icon="chevron-up"
                data-move={`${id}:-1`}
                data-moving={id}
                disabled={index === 0}
                aria-label={fill(exerciseCopy.moveUp, { n: index + 1 }).nl}
                onClick={() => move(id, -1)}
              />
              <Button
                variant="ghost"
                size="small"
                icon="chevron-down"
                data-move={`${id}:1`}
                data-moving={id}
                disabled={index === order.length - 1}
                aria-label={fill(exerciseCopy.moveDown, { n: index + 1 }).nl}
                onClick={() => move(id, 1)}
              />
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
