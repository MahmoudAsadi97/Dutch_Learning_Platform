"use client";

import { LearningText, type LearningCopy } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { dutchSentences } from "@/lib/client/sentences";

/** A Dutch text sentence by sentence, each one to hear; its translation only when the text carries one.
 * Sentence replay remains separate from translations and from final tests. */
export function SpokenPassage({ text }: { text: LearningCopy }) {
  const paragraphs = text.nl.split(/\n\s*\n/).filter(Boolean);
  return (
    <div className="spoken-passage">
      <div lang="nl">
        {paragraphs.map((paragraph, i) => (
          <p key={i}>
            {dutchSentences(paragraph).map((sentence, j) => (
              <span className="spoken-sentence" key={j}>
                <span>{sentence.trim()} </span>
                <PhraseAudio text={sentence.trim()} />{" "}
              </span>
            ))}
          </p>
        ))}
      </div>
      <LearningText text={text} supportOnly />
    </div>
  );
}
