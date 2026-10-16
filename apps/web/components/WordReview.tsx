"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { useLanguageSupport } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { SpokenText } from "@/components/SpokenPassage";
import { errorCopy } from "@/lib/client/error-copy";
import { isAbort } from "@/lib/client/errors";
import { words, type Grade, type WordItem, type WordStats } from "@/lib/client/stories";
import { wordsCopy } from "@/lib/copy/words";
import { fill, uiCopy, type Copy } from "@/lib/ui-copy";
import { Skeleton, SkeletonPanel } from "@/components/ui";
import { ButtonLink, EmptyState } from "@/components/ui";
import { UiText } from "@/components/ui/UiText";

const gradeCopy: { grade: Grade; label: Copy; hint: Copy }[] = [
  { grade: "again", label: wordsCopy.gradeAgain, hint: wordsCopy.gradeAgainHint },
  { grade: "hard", label: wordsCopy.gradeHard, hint: wordsCopy.gradeHardHint },
  { grade: "good", label: wordsCopy.gradeGood, hint: wordsCopy.gradeGoodHint },
  { grade: "easy", label: wordsCopy.gradeEasy, hint: wordsCopy.gradeEasyHint },
];

export function WordReview() {
  const [queue, setQueue] = useState<WordItem[] | null>(null);
  const [stats, setStats] = useState<WordStats | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [done, setDone] = useState(0);
  const [error, setError] = useState<Copy | null>(null);
  const [allWords, setAllWords] = useState<WordItem[] | null>(null);
  const [draft, setDraft] = useState({ term: "", meaning_en: "", meaning_fa: "" });
  const [notice, setNotice] = useState<Copy | null>(null);
  const { showEnglish, showPersian } = useLanguageSupport();
  const load = useCallback(
    (signal?: AbortSignal) =>
      words
        .due(20, signal)
        .then((due) => {
          setQueue(due.items);
          setStats(due);
          setRevealed(false);
        })
        .catch((cause) => {
          if (!isAbort(cause)) setError(errorCopy(cause, wordsCopy.loadFailed, undefined, "load"));
        }),
    [],
  );
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  async function grade(item: WordItem, value: Grade) {
    try {
      const updated = await words.review(item.id, value);
      setDone((count) => count + 1);
      setQueue((current) => {
        const rest = (current ?? []).filter((entry) => entry.id !== item.id);
        return updated.due ? [...rest, updated] : rest; // "again" returns the card to the end of the session
      });
      setStats((current) =>
        current ? { ...current, due_count: Math.max(0, current.due_count - (updated.due ? 0 : 1)) } : current,
      );
      setRevealed(false);
    } catch (cause) {
      setError(errorCopy(cause, wordsCopy.gradeFailed));
    }
  }
  async function toggleAll() {
    if (allWords) {
      setAllWords(null);
      return;
    }
    try {
      setAllWords((await words.all()).items);
    } catch (cause) {
      setError(errorCopy(cause, wordsCopy.listFailed, undefined, "load"));
    }
  }
  async function add() {
    if (!draft.term.trim()) return;
    try {
      const result = await words.save(draft.term.trim(), draft.meaning_en.trim(), draft.meaning_fa.trim());
      setNotice(
        fill(result.created ? wordsCopy.savedNew : wordsCopy.savedAlready, { term: result.item.term }),
      );
      setDraft({ term: "", meaning_en: "", meaning_fa: "" });
      await load();
      if (allWords) setAllWords((await words.all()).items);
    } catch (cause) {
      setNotice(errorCopy(cause, wordsCopy.saveFailed, undefined, "input"));
    }
  }

  if (error)
    return (
      <div className="error" role="alert">
        <UiText text={error} tier="guide" inline />{" "}
        <button
          className="linklike"
          onClick={() => {
            setError(null);
            void load();
          }}
        >
          <UiText text={uiCopy.action.retry} inline />
        </button>
      </div>
    );
  if (!queue || !stats)
    return (
      <SkeletonPanel label={wordsCopy.loading.nl}>
        <Skeleton lines={3} />
      </SkeletonPanel>
    );
  const current = queue[0];
  const counts = { total: stats.total, learned: stats.learned_count, due: stats.due_count, done };
  return (
    <div className="word-review" data-testid="word-review">
      <header className="path-heading">
        <div>
          <p className="eyebrow">
            <UiText text={wordsCopy.eyebrow} />
          </p>
          <h1>
            <UiText
              text={current ? wordsCopy.titleReview : done ? wordsCopy.titleDone : wordsCopy.titleNothing}
            />
          </h1>
          <p className="muted">
            <UiText text={fill(done ? wordsCopy.statsWithDone : wordsCopy.stats, counts)} />
          </p>
        </div>
        <Link className="button secondary" href="/">
          <UiText text={uiCopy.nav.today} inline />
          <Icon name="arrow" size={16} />
        </Link>
      </header>

      {current ? (
        <section className="flashcard" aria-live="polite">
          <p className="eyebrow">
            <UiText
              text={fill(queue.length === 1 ? wordsCopy.cardsOne : wordsCopy.cardsMany, {
                count: queue.length,
              })}
            />
          </p>
          <div className="flashcard-face">
            <p className="flashcard-term" lang="nl">
              {current.term} <PhraseAudio text={current.term} />
            </p>
            {revealed ? (
              <div className="flashcard-back">
                <p className="flashcard-meaning">
                  {showEnglish && <span lang="en">{current.meaning_en}</span>}
                  {showEnglish && showPersian && current.meaning_fa && <span aria-hidden="true"> · </span>}
                  {showPersian && (
                    <span lang="fa" dir="rtl" className="fa">
                      {current.meaning_fa}
                    </span>
                  )}
                  {!showEnglish && !showPersian && <span lang="en">{current.meaning_en}</span>}
                </p>
                {current.example && (
                  <p lang="nl" className="muted">
                    <SpokenText text={{ nl: current.example }} />
                  </p>
                )}
                <div className="grade-buttons" role="group" aria-label={wordsCopy.gradeQuestion.nl}>
                  {gradeCopy.map((option) => (
                    <button
                      key={option.grade}
                      type="button"
                      className={`grade-button grade-${option.grade}`}
                      onClick={() => void grade(current, option.grade)}
                    >
                      <strong>
                        <UiText text={option.label} inline />
                      </strong>
                      <small>
                        <UiText text={option.hint} inline />
                      </small>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <button
                className="button"
                type="button"
                data-testid="reveal-word"
                onClick={() => setRevealed(true)}
              >
                <UiText text={uiCopy.action.showMeaning} inline />
              </button>
            )}
          </div>
          <p className="small-text muted">
            <UiText text={wordsCopy.intervalNote} tier="guide" />
          </p>
        </section>
      ) : (
        <EmptyState
          icon={done ? "check" : "star"}
          accent="words"
          title={<UiText text={done ? wordsCopy.emptyDoneTitle : wordsCopy.emptyNoneTitle} />}
          description={
            <UiText text={done ? wordsCopy.emptyDoneText : wordsCopy.emptyNoneText} tier="guide" />
          }
        >
          <ButtonLink href="/verhalen" icon="arrow" iconEnd>
            <UiText text={wordsCopy.toStories} inline />
          </ButtonLink>
        </EmptyState>
      )}

      <section className="wish-card inline" aria-labelledby="add-word">
        <h2 id="add-word">
          <UiText text={wordsCopy.addTitle} />
        </h2>
        <form
          className="word-form"
          onSubmit={(event) => {
            event.preventDefault();
            void add();
          }}
        >
          <label>
            <UiText text={wordsCopy.fieldWord} />
            <input
              lang="nl"
              value={draft.term}
              onChange={(event) => setDraft({ ...draft, term: event.target.value })}
              maxLength={120}
              placeholder={wordsCopy.example.nl}
            />
          </label>
          <label>
            <UiText text={wordsCopy.fieldEnglish} />
            <input
              lang="en"
              value={draft.meaning_en}
              onChange={(event) => setDraft({ ...draft, meaning_en: event.target.value })}
              maxLength={300}
              placeholder={wordsCopy.example.en}
            />
          </label>
          <label>
            <UiText text={wordsCopy.fieldPersian} />
            <input
              lang="fa"
              dir="rtl"
              value={draft.meaning_fa}
              onChange={(event) => setDraft({ ...draft, meaning_fa: event.target.value })}
              maxLength={300}
              placeholder={wordsCopy.example.fa}
            />
          </label>
          <button className="button secondary" type="submit" disabled={!draft.term.trim()}>
            <UiText text={uiCopy.action.save} inline />
          </button>
        </form>
        {notice && (
          <p className="practice-hint" role="status">
            <UiText text={notice} tier="guide" />
          </p>
        )}
      </section>

      <button type="button" className="linklike" onClick={() => void toggleAll()}>
        <UiText text={allWords ? wordsCopy.hideList : wordsCopy.showList} inline />
      </button>
      {allWords && (
        <ul className="word-list">
          {allWords.map((item) => (
            <li key={item.id}>
              <strong lang="nl">{item.term}</strong>{" "}
              <span className="muted">
                {item.meaning_en}
                {item.meaning_fa ? ` · ${item.meaning_fa}` : ""}
              </span>
              <span className="small-text muted">
                <UiText
                  text={
                    item.learned
                      ? wordsCopy.statusLearned
                      : item.due
                        ? wordsCopy.statusDue
                        : fill(item.interval_days === 1 ? wordsCopy.backInDay : wordsCopy.backInDays, {
                            days: item.interval_days,
                          })
                  }
                  inline
                />
              </span>
              <button
                type="button"
                className="linklike"
                onClick={() =>
                  void words
                    .remove(item.id)
                    .then(() => Promise.all([load(), words.all().then((all) => setAllWords(all.items))]))
                    .catch((cause) => setNotice(errorCopy(cause, wordsCopy.removeFailed)))
                }
              >
                {/* the visible label starts the accessible name; the word says which one goes */}
                <UiText text={wordsCopy.remove} inline />{" "}
                <span className="visually-hidden" lang="nl">
                  {item.term}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
