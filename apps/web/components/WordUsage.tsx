"use client";

import { useState } from "react";
import { LearningText } from "@/components/LanguageSupport";
import { SpokenText } from "@/components/SpokenPassage";
import type { LibraryWord } from "@/lib/client/library";
import { storyLearningCopy } from "@/lib/copy/storyLearning";
import { fill } from "@/lib/ui-copy";

const wordTypes = {
  noun: storyLearningCopy.noun,
  verb: storyLearningCopy.verb,
  adjective: storyLearningCopy.adjective,
  adverb: storyLearningCopy.adverb,
  expression: storyLearningCopy.expression,
  other: storyLearningCopy.other,
};

/** Authored examples stay attached to the word; personal practice is not scored as mastery. */
export function WordUsage({ word }: { word: Omit<LibraryWord, "topic"> }) {
  const [contextIndex, setContextIndex] = useState(0);
  const [ownSentence, setOwnSentence] = useState("");
  const contexts = word.contexts ?? [];
  const context = contexts[contextIndex % (contexts.length || 1)];
  if (!word.forms?.length && !contexts.length && !word.article && !word.plural && !word.part_of_speech)
    return null;
  return (
    <div className="word-usage">
      {word.part_of_speech && wordTypes[word.part_of_speech] && (
        <p className="word-type small-text muted">
          <LearningText text={wordTypes[word.part_of_speech]} />
        </p>
      )}
      {(word.article || word.plural) && (
        <p className="word-shape" lang="nl">
          {word.article && (
            <span>
              {word.article} {word.term.replace(/^(de|het) /u, "")}
            </span>
          )}
          {word.article && word.plural && <span aria-hidden="true"> · </span>}
          {word.plural && <span>{word.plural}</span>}
        </p>
      )}
      {!!word.forms?.length && (
        <details>
          <summary>
            <LearningText text={storyLearningCopy.wordForms} />
          </summary>
          <dl className="word-forms">
            {word.forms.map((form, index) => (
              <div key={`${form.label.nl}-${index}`}>
                <dt>
                  <LearningText text={form.label} />
                </dt>
                <dd>
                  <SpokenText text={form.text} />
                </dd>
              </div>
            ))}
          </dl>
        </details>
      )}
      {context && (
        <section
          className="word-context"
          aria-label={fill(storyLearningCopy.wordContext, { term: word.term }).nl}
        >
          <p className="eyebrow">
            <LearningText text={context.setting} />
          </p>
          <div className="word-context-example">
            <SpokenText text={context.sentence} />
          </div>
          {contexts.length > 1 && (
            <button
              type="button"
              className="linklike"
              onClick={() => {
                setContextIndex((value) => value + 1);
                setOwnSentence("");
              }}
            >
              <LearningText text={storyLearningCopy.anotherContext} />
              <span className="visually-hidden">
                {" "}
                ({(contextIndex % contexts.length) + 1} / {contexts.length})
              </span>
            </button>
          )}
          <label className="word-context-prompt">
            <LearningText text={context.production_prompt} />
            <textarea
              lang="nl"
              value={ownSentence}
              onChange={(event) => setOwnSentence(event.target.value)}
              maxLength={1000}
              rows={2}
              placeholder={storyLearningCopy.ownSentence.nl}
            />
          </label>
          <p className="small-text muted">
            <LearningText text={storyLearningCopy.wordScratch} />
          </p>
        </section>
      )}
    </div>
  );
}
