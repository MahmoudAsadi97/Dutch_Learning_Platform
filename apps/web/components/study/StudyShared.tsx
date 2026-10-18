"use client";

import { useCallback, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { LearningText, useLanguageSupport } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { SpokenText } from "@/components/SpokenPassage";
import { apiJson } from "@/lib/client/api";
import { friendlyError } from "@/lib/client/curriculum";
import type { LibraryPage, LibraryWord } from "@/lib/client/library";
import type { StudyWord } from "@/lib/client/study";
import { studyCopy, studyWordClasses } from "@/lib/copy/study";

export function StudyError({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="study-error" role="alert">
      <Icon name="alert" size={19} />
      <div>
        <p>{message}</p>
        {retry && (
          <button type="button" className="study-text-button" onClick={retry}>
            <LearningText text={studyCopy.retry} />{" "}
          </button>
        )}
      </div>
    </div>
  );
}

export function CompactWords({ words }: { words: StudyWord[] }) {
  const { showEnglish } = useLanguageSupport();
  return (
    <div className="study-word-grid">
      {words.map((word, index) => (
        <article className="study-word" key={`${word.id}-${index}`}>
          <div className="study-word-top">
            <strong lang="nl">{word.term}</strong>
            <PhraseAudio text={word.term} />
          </div>
          {word.part_of_speech && (
            <span className="study-word-class">
              {studyWordClasses[word.part_of_speech] ?? word.part_of_speech}
            </span>
          )}
          {(word.meaning.nl !== word.term || (showEnglish && word.meaning.en)) && (
            <p className="study-word-meaning">
              <LearningText
                text={word.meaning.nl === word.term ? { nl: "", en: word.meaning.en } : word.meaning}
              />
            </p>
          )}
          <div className="study-word-example">
            <SpokenText text={word.example} />
          </div>
          {word.forms?.length || word.contexts?.length ? (
            <details className="study-word-extra">
              <summary>
                {" "}
                <LearningText text={studyCopy.moreExamples} />{" "}
              </summary>
              {word.forms?.map((form) => (
                <p key={`${form.label.nl}.${form.text.nl}`}>
                  <small>
                    <LearningText text={form.label} />
                  </small>{" "}
                  <SpokenText text={form.text} />
                </p>
              ))}
              {word.contexts?.map((context) => (
                <div key={context.id}>
                  <small>
                    <LearningText text={context.setting} />
                  </small>
                  <SpokenText text={context.sentence} />
                </div>
              ))}
            </details>
          ) : null}
        </article>
      ))}
    </div>
  );
}

/** The full existing word collection remains reachable without becoming another top-level destination. */
export function WordReference({ stageId }: { stageId: string }) {
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [loaded, setLoaded] = useState<{ requestKey: string; page: LibraryPage<LibraryWord> } | null>(null);
  const requestKey = `${stageId}.${query}.${offset}`;
  const page = loaded?.requestKey === requestKey ? loaded.page : null;
  const setPage = useCallback(
    (page: LibraryPage<LibraryWord> | null) => setLoaded(page ? { requestKey, page } : null),
    [requestKey],
  );
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<LibraryPage<LibraryWord>>(
      `library/${stageId}/vocabulary?${new URLSearchParams({ q: query, offset: String(offset), limit: "18" })}`,
      { signal: controller.signal },
    )
      .then((value) => {
        if (controller.signal.aborted) return;
        setPage(value);
        setError("");
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(friendlyError(cause, "load"));
      });
    return () => controller.abort();
  }, [stageId, query, offset, retry, setPage]);
  return (
    <section className="study-reference" aria-label={studyCopy.wordReferenceRegion.nl}>
      <label className="study-search">
        <Icon name="search" size={18} />
        <input
          value={query}
          onChange={(event) => {
            setPage(null);
            setError("");
            setQuery(event.target.value);
            setOffset(0);
          }}
          placeholder={studyCopy.searchWordPlaceholder.nl}
          aria-label={studyCopy.searchWordLabel.nl}
          maxLength={120}
        />
      </label>
      {error ? (
        <StudyError message={error} retry={() => setRetry((value) => value + 1)} />
      ) : page ? (
        <>
          <CompactWords words={page.items} />
          <div className="study-pagination">
            <button
              className="button secondary"
              disabled={offset === 0}
              onClick={() => {
                setPage(null);
                setOffset(Math.max(0, offset - 18));
              }}
            >
              <LearningText text={studyCopy.previous} />{" "}
            </button>
            <button
              className="button secondary"
              disabled={offset + page.limit >= page.total}
              onClick={() => {
                setPage(null);
                setOffset(offset + 18);
              }}
            >
              <LearningText text={studyCopy.nextWords} /> <Icon name="arrow" size={16} />
            </button>
          </div>
          {page.items.length === 0 && (
            <p>
              {" "}
              <LearningText text={studyCopy.noWords} />{" "}
            </p>
          )}
        </>
      ) : (
        <p role="status">
          {" "}
          <LearningText text={studyCopy.loadingWords} />{" "}
        </p>
      )}
    </section>
  );
}
