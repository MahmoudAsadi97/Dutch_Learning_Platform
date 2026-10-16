"use client";

import { LearningText, type LearningCopy } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { dutchSentences } from "@/lib/client/sentences";

/** For controls whose text is already a label; playback must not sit inside the clickable label. */
export function SentenceAudio({ text, disabled = false }: { text: string; disabled?: boolean }) {
  return (
    <span className="sentence-audio-controls">
      {dutchSentences(text)
        .filter((sentence) => sentence.trim())
        .map((sentence, i) => (
          <PhraseAudio key={i} text={sentence.trim()} disabled={disabled} />
        ))}
    </span>
  );
}

/** A Dutch text sentence by sentence, each one to hear; its translation only when the text carries one.
 * Sentence replay remains separate from translations and from final tests. */
export function SpokenText({ text, disabled = false }: { text: LearningCopy; disabled?: boolean }) {
  return (
    <span className="spoken-text">
      <span lang="nl">
        {dutchSentences(text.nl).map((sentence, i) => (
          <span className="spoken-sentence" key={i}>
            <span>{sentence.trim()} </span>
            <PhraseAudio text={sentence.trim()} disabled={disabled} />{" "}
          </span>
        ))}
      </span>
      <LearningText text={text} supportOnly />
    </span>
  );
}

export function SpokenPassage({ text, disabled = false }: { text: LearningCopy; disabled?: boolean }) {
  const paragraphs = text.nl.split(/\n\s*\n/).filter(Boolean);
  return (
    <div className="spoken-passage">
      <div lang="nl">
        {paragraphs.map((paragraph, i) => (
          <p key={i}>
            {dutchSentences(paragraph).map((sentence, j) => (
              <span className="spoken-sentence" key={j}>
                <span>{sentence.trim()} </span>
                <PhraseAudio text={sentence.trim()} disabled={disabled} />{" "}
              </span>
            ))}
          </p>
        ))}
      </div>
      <LearningText text={text} supportOnly />
    </div>
  );
}
