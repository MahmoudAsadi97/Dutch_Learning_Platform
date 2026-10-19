"use client";

import { useEffect, useId, useState } from "react";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { SpokenText } from "@/components/SpokenPassage";
import type { StudyWord } from "@/lib/client/study";
import {
  studyWordTransferCopy as copy,
  wordTransferPosition,
  wordTransferResponseLabel,
} from "@/lib/copy/studyWordTransfer";

type WordContext = NonNullable<StudyWord["contexts"]>[number];

/** Authored uses supplement the source example; this scratch space never grades or saves a draft. */
export function WordTransferPractice({ word }: { word: StudyWord }) {
  const [pageEpoch, setPageEpoch] = useState(0);
  useEffect(() => {
    const clear = (event: PageTransitionEvent) => {
      if (event.persisted) setPageEpoch((value) => value + 1);
    };
    window.addEventListener("pageshow", clear);
    return () => window.removeEventListener("pageshow", clear);
  }, []);
  return <WordTransferDetails key={JSON.stringify([pageEpoch, word])} word={word} />;
}

function WordTransferDetails({ word }: { word: StudyWord }) {
  const [contextIndex, setContextIndex] = useState(0);
  const authoredForms = word.forms?.filter((form) => form.text.nl.trim()) ?? [];
  const plural = word.plural?.trim();
  const forms =
    plural && !authoredForms.some((form) => form.text.nl.trim() === plural)
      ? [...authoredForms, { label: copy.plural, text: { nl: plural } }]
      : authoredForms;
  const contexts = word.contexts?.filter((context) => context.sentence.nl.trim()) ?? [];
  const context = contexts[contextIndex];
  if (!forms.length && !contexts.length) return null;

  return (
    <details className="study-word-transfer">
      <summary>
        <LearningText text={contexts.length ? copy.moreUses : copy.formsOnly} />
      </summary>
      {forms.length > 0 && (
        <section className="study-word-transfer-forms" aria-label={copy.forms.nl}>
          <h4>
            <LearningText text={copy.forms} />
          </h4>
          <dl>
            {forms.map((form, index) => (
              <div key={`${form.label.nl}.${index}`}>
                <dt>
                  <LearningText text={form.label} />
                </dt>
                <dd>
                  <SpokenText text={form.text} />
                </dd>
              </div>
            ))}
          </dl>
        </section>
      )}
      {context && (
        <section className="study-word-transfer-context" aria-label={copy.moreUses.nl}>
          <div className="study-word-transfer-context-heading">
            <h4>
              <LearningText text={context.setting} />
            </h4>
            {contexts.length > 1 && (
              <span className="study-word-transfer-position" role="status">
                <LearningText text={wordTransferPosition(contextIndex + 1, contexts.length)} />
              </span>
            )}
          </div>
          <ContextAttempt
            key={`${contextIndex}.${JSON.stringify(context)}`}
            context={context}
            term={word.term}
          />
          {contexts.length > 1 && (
            <button
              type="button"
              className="study-word-transfer-next"
              onClick={() => setContextIndex((value) => (value + 1) % contexts.length)}
            >
              <LearningText text={copy.anotherSituation} />
              <Icon name="arrow" size={16} />
            </button>
          )}
        </section>
      )}
    </details>
  );
}

function ContextAttempt({ context, term }: { context: WordContext; term: string }) {
  const [draft, setDraft] = useState("");
  const [revealed, setRevealed] = useState(false);
  const id = useId();
  const prompt = context.production_prompt;
  if (!prompt?.nl.trim())
    return (
      <div className="study-word-transfer-example">
        <SpokenText text={context.sentence} />
      </div>
    );

  return (
    <div className="study-word-transfer-attempt">
      <p className="study-word-transfer-prompt">
        <SpokenText text={prompt} />
      </p>
      <p className="study-word-transfer-guidance">
        <LearningText text={copy.tryFirst} />
      </p>
      <label htmlFor={`${id}-draft`}>
        <LearningText text={wordTransferResponseLabel(term)} />
      </label>
      <textarea
        id={`${id}-draft`}
        lang="nl"
        rows={2}
        maxLength={1000}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        aria-describedby={`${id}-temporary`}
      />
      <p id={`${id}-temporary`} className="study-word-transfer-temporary">
        <LearningText text={copy.temporaryDraft} />
      </p>
      <button
        type="button"
        className="study-word-transfer-reveal"
        aria-expanded={revealed}
        aria-controls={`${id}-example`}
        onClick={() => setRevealed((value) => !value)}
      >
        <LearningText text={revealed ? copy.hideExample : copy.showExample} />
      </button>
      <div id={`${id}-example`} hidden={!revealed} className="study-word-transfer-example">
        {revealed && (
          <>
            <p className="study-word-transfer-example-label">
              <LearningText text={copy.example} />
            </p>
            <SpokenText text={context.sentence} />
          </>
        )}
      </div>
    </div>
  );
}
