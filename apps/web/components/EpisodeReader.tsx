"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";
import { useLanguageSupport } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { SentenceAudio, SpokenText } from "@/components/SpokenPassage";
import { Cover, Skeleton, SkeletonPanel } from "@/components/ui";
import { newRequestId } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { isAbort } from "@/lib/client/errors";
import { useRecorder } from "@/lib/client/recorder";
import { stageLabels, stories, type Episode, type GlossaryItem } from "@/lib/client/stories";
import { playTone } from "@/lib/client/tones";
import { HonestyChip } from "@/components/ui/HonestyChip";
import { UiText } from "@/components/ui/UiText";
import { episodeCopy } from "@/lib/copy/episode";
import { fill, uiCopy, type Copy } from "@/lib/ui-copy";

export function EpisodeReader({ episodeId }: { episodeId: string }) {
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [error, setError] = useState<Copy | null>(null);
  const [finished, setFinished] = useState(false);
  const [notice, setNotice] = useState<Copy | null>(null);
  const load = useCallback(
    (signal?: AbortSignal) =>
      stories
        .episode(episodeId, signal)
        .then((value) => {
          setEpisode(value);
          setFinished(Boolean(value.read_at));
        })
        .catch((cause) => {
          if (!isAbort(cause))
            setError(errorCopy(cause, episodeCopy.loadFailed, { 404: episodeCopy.notFound }, "load"));
        }),
    [episodeId],
  );
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  if (error)
    return (
      <div className="error" role="alert">
        <UiText text={error} tier="guide" inline />{" "}
        <Link href="/verhalen">
          <UiText text={episodeCopy.toStories} inline />
        </Link>
      </div>
    );
  if (!episode)
    return (
      <SkeletonPanel label={episodeCopy.loading.nl}>
        <Skeleton lines={3} />
      </SkeletonPanel>
    );
  if (episode.status !== "ready")
    return (
      <div className="card">
        <p className="eyebrow">
          <UiText text={fill(episodeCopy.episodeNumber, { number: episode.number })} />
        </p>
        <h1>
          <UiText
            text={episode.status === "failed" ? episodeCopy.episodeFailed : episodeCopy.episodeWriting}
          />
        </h1>
        <p className="muted">
          {/* one sentence, so the gloss reads whole; the link covers it instead of "Vandaag" alone */}
          <Link href="/">
            <UiText text={episodeCopy.checkStatus} tier="guide" inline />
          </Link>
        </p>
      </div>
    );

  return (
    <article className="episode-reader" data-testid="episode-reader">
      <header className="episode-header">
        <Cover number={episode.number} caption="De Lindestraat" />
        <div>
          <p className="eyebrow">
            <UiText
              text={fill(episodeCopy.episodeMeta, {
                number: episode.number,
                stage: stageLabels[episode.stage_id] ?? episode.stage_id,
                words: episode.word_count,
              })}
            />
          </p>
          <h1>{episode.title}</h1>
          <p className="muted">
            <UiText text={episodeCopy.theme} inline /> {episode.theme}
            {episode.previous_choice && (
              <>
                {" "}
                · <UiText text={episodeCopy.previousChoice} inline /> <em>{episode.previous_choice}</em>
              </>
            )}
          </p>
          <div className="episode-tools">
            <PhraseAudio
              text={episode.paragraphs.map((p) => p.nl).join(" ")}
              label={episodeCopy.wholeEpisode.nl}
            />
            <span className="small-text muted">
              <UiText text={episodeCopy.listenHint} tier="guide" />
            </span>
          </div>
        </div>
      </header>

      <div className="episode-body">
        {episode.paragraphs.map((paragraph, index) => (
          <Paragraph
            key={index}
            episodeId={episode.id}
            index={index}
            nl={paragraph.nl}
            en={paragraph.en}
            fa={paragraph.fa}
            onTranslated={(fa) =>
              setEpisode((current) =>
                current
                  ? {
                      ...current,
                      paragraphs: current.paragraphs.map((p, i) => (i === index ? { ...p, fa } : p)),
                    }
                  : current,
              )
            }
            attempts={episode.read_aloud[String(index)]}
            onReadAloud={() => void load()}
          />
        ))}
      </div>

      <Glossary episodeId={episode.id} items={episode.glossary} />

      {!finished && (
        <div className="finish-row">
          <button
            className="button"
            data-testid="finish-reading"
            onClick={() => {
              setFinished(true);
              void stories
                .read(episode.id)
                .then(setEpisode)
                .catch(() => undefined);
            }}
          >
            <UiText text={episodeCopy.finishReading} inline />
            <Icon name="arrow" size={18} />
          </button>
          <span className="small-text muted">
            <UiText text={episodeCopy.finishHint} tier="guide" />
          </span>
        </div>
      )}

      {finished && (
        <>
          <Questions episode={episode} onUpdate={setEpisode} />
          <section className="episode-choice" id="keuze" aria-labelledby="choice-title">
            <p className="eyebrow">
              <UiText text={episodeCopy.yourChoice} />
            </p>
            <h2 id="choice-title">
              <UiText
                text={episode.chosen_choice ? episodeCopy.nextBeingWritten : episodeCopy.howItContinues}
              />
            </h2>
            {!episode.chosen_choice && (
              <p className="muted">
                <UiText text={episodeCopy.writerUsesChoice} tier="guide" />
              </p>
            )}
            <div className="choice-buttons">
              {episode.choices.map((choice) => (
                <div key={choice.id} className="story-choice-audio">
                  <button
                    type="button"
                    className={`choice-button ${episode.chosen_choice === choice.id ? "is-chosen" : ""}`}
                    disabled={Boolean(episode.chosen_choice)}
                    aria-pressed={episode.chosen_choice === choice.id}
                    onClick={() =>
                      void stories
                        .choose(episode.id, choice.id)
                        .then(setEpisode)
                        .catch((cause) => setNotice(errorCopy(cause, episodeCopy.choiceFailed)))
                    }
                  >
                    <span className="choice-letter" aria-hidden="true">
                      {choice.id.toUpperCase()}
                    </span>
                    <span lang="nl">{choice.label}</span>
                  </button>
                  <SentenceAudio text={choice.label} />
                </div>
              ))}
            </div>
            {episode.chosen_choice && (
              <p className="practice-complete" role="status">
                <UiText text={episodeCopy.choicePassed} tier="guide" inline />{" "}
                <UiText text={episodeCopy.newEpisodeOnToday} tier="guide" inline />{" "}
                <Link href="/">
                  <UiText text={episodeCopy.backToToday} inline />
                </Link>
              </p>
            )}
            {notice && (
              <p className="error" role="alert">
                <UiText text={notice} tier="guide" />
              </p>
            )}
          </section>
          <footer className="episode-footer">
            <div className="rating" role="group" aria-label={episodeCopy.ratingGroup.nl}>
              <span className="small-text muted">
                <UiText text={episodeCopy.ratingQuestion} inline />
              </span>
              <button
                type="button"
                className={`linklike ${episode.rating === 1 ? "is-on" : ""}`}
                aria-pressed={episode.rating === 1}
                onClick={() =>
                  void stories
                    .rate(episode.id, 1)
                    .then(setEpisode)
                    .catch(() => undefined)
                }
              >
                <UiText text={episodeCopy.yes} inline />
              </button>
              <button
                type="button"
                className={`linklike ${episode.rating === -1 ? "is-on" : ""}`}
                aria-pressed={episode.rating === -1}
                onClick={() =>
                  void stories
                    .rate(episode.id, -1)
                    .then(setEpisode)
                    .catch(() => undefined)
                }
              >
                <UiText text={episodeCopy.notReally} inline />
              </button>
            </div>
            {episode.topic_id && (
              <Link
                className="stage-link"
                href={`/learn/${episode.stage_id}?skill=reading&topic=${episode.topic_id}`}
              >
                <UiText text={episodeCopy.practiseTopic} inline />
                <Icon name="arrow" size={17} />
              </Link>
            )}
            <div className="honesty-row">
              <HonestyChip
                kind="generated"
                detail={`${episode.model || episode.provider}; automatische controle: ${episode.warnings.length} aandachtspunten`}
              />
            </div>
          </footer>
        </>
      )}
    </article>
  );
}

function Paragraph({
  episodeId,
  index,
  nl,
  en,
  fa,
  onTranslated,
  attempts,
  onReadAloud,
}: {
  episodeId: string;
  index: number;
  nl: string;
  en: string;
  fa?: string;
  onTranslated: (fa: string) => void;
  attempts?: { matched_words: number; target_words: number; attempts: number };
  onReadAloud: () => void;
}) {
  const { showEnglish, showPersian } = useLanguageSupport();
  const [translating, setTranslating] = useState(false);
  const [message, setMessage] = useState<Copy | null>(null);
  return (
    <section className="episode-paragraph" data-testid="episode-paragraph">
      <p lang="nl" className="story-copy">
        <SpokenText text={{ nl }} />
      </p>
      {showEnglish && en && (
        <p lang="en" className="copy-support">
          {en}
        </p>
      )}
      {showPersian &&
        (fa ? (
          <p lang="fa" dir="rtl" className="copy-support fa">
            {fa}
          </p>
        ) : (
          <button
            type="button"
            className="linklike"
            disabled={translating}
            onClick={() => {
              setTranslating(true);
              setMessage(null);
              void stories
                .translate(episodeId, index)
                .then((result) => onTranslated(result.fa))
                .catch((cause) => setMessage(errorCopy(cause, episodeCopy.translateFailed)))
                .finally(() => setTranslating(false));
            }}
          >
            <UiText text={translating ? episodeCopy.translating : episodeCopy.translate} inline />
          </button>
        ))}
      <ReadAloud episodeId={episodeId} index={index} attempts={attempts} onDone={onReadAloud} />
      {message && (
        <p className="error" role="alert">
          <UiText text={message} tier="guide" />
        </p>
      )}
    </section>
  );
}

function ReadAloud({
  episodeId,
  index,
  attempts,
  onDone,
}: {
  episodeId: string;
  index: number;
  attempts?: { matched_words: number; target_words: number; attempts: number };
  onDone: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{
    matched: number;
    target: number;
    missed: string[];
    points: number;
  } | null>(null);
  const [error, setError] = useState<Copy | null>(null);
  const uploadRef = useRef<AbortController | null>(null);
  // Leaving the episode lets an upload in flight finish: the attempt counts either way, and only a finished
  // request can announce the day's goal. Its result is just no longer shown.
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const recorder = useRecorder((recording) => {
    uploadRef.current?.abort();
    const request = new AbortController();
    uploadRef.current = request;
    setBusy(true);
    setError(null);
    void stories
      .readAloud(episodeId, index, recording.blob, recording.fileName, request.signal)
      .then((value) => {
        if (mounted.current && !request.signal.aborted) {
          setResult({
            matched: value.matched_words,
            target: value.target_words,
            missed: value.missed,
            points: value.points,
          });
          onDone();
        }
      })
      .catch((cause) => {
        if (mounted.current && !request.signal.aborted)
          setError(errorCopy(cause, episodeCopy.recordingFailed, { 422: episodeCopy.recordingFailed }));
      })
      .finally(() => {
        if (mounted.current && uploadRef.current === request) setBusy(false);
      });
  });
  const recording = recorder.phase === "recording";
  if (recorder.phase === "unsupported") return null;
  return (
    <div className={`read-aloud ${recording ? "is-recording" : ""}`}>
      <button
        type="button"
        className="button secondary"
        aria-pressed={recording}
        disabled={busy}
        onClick={() => {
          if (recording) recorder.stop();
          else void recorder.start();
        }}
      >
        <Icon name="mic" size={16} />
        <UiText
          text={
            recording
              ? episodeCopy.stop
              : busy
                ? episodeCopy.listening
                : result || attempts
                  ? episodeCopy.readAgain
                  : episodeCopy.readAloud
          }
          inline
        />
      </button>
      {result && (
        <span className="read-aloud-result" role="status">
          <UiText
            text={fill(result.points ? episodeCopy.recognisedPoints : episodeCopy.recognised, {
              matched: result.matched,
              target: result.target,
              points: result.points,
            })}
            inline
          />
          {result.missed.length > 0 && (
            <>
              {" "}
              <UiText text={episodeCopy.practiseMore} inline />{" "}
              <em lang="nl">{result.missed.slice(0, 8).join(", ")}</em>
            </>
          )}
        </span>
      )}
      {!result && attempts && (
        <span className="read-aloud-result muted">
          <UiText
            text={fill(episodeCopy.earlier, {
              matched: attempts.matched_words,
              target: attempts.target_words,
            })}
            inline
          />
        </span>
      )}
      {(error || recorder.error) && (
        <span className="error" role="alert">
          <UiText text={error ?? episodeCopy.micAccess} tier="guide" inline />
        </span>
      )}
    </div>
  );
}

function Glossary({ episodeId, items }: { episodeId: string; items: GlossaryItem[] }) {
  const { showEnglish, showPersian } = useLanguageSupport();
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState<Copy | null>(null);
  if (!items.length) return null;
  return (
    <section className="episode-glossary" aria-labelledby="glossary-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">
            <UiText text={episodeCopy.newWords} />
          </p>
          <h2 id="glossary-title">
            <UiText text={episodeCopy.glossaryTitle} />
          </h2>
        </div>
        <span className="quiet-badge">
          <UiText text={fill(episodeCopy.wordCount, { count: items.length })} inline />
        </span>
      </div>
      <ul className="glossary-list">
        {items.map((item) => (
          <li key={item.term} className="glossary-item">
            <div className="glossary-term">
              <strong lang="nl">{item.term}</strong>
              <PhraseAudio text={item.term} />
            </div>
            <div className="glossary-meaning">
              {showEnglish && <span lang="en">{item.meaning_en}</span>}
              {showEnglish && showPersian && <span aria-hidden="true"> · </span>}
              {showPersian && (
                <span lang="fa" dir="rtl" className="fa">
                  {item.meaning_fa}
                </span>
              )}
              {!showEnglish && !showPersian && <span lang="en">{item.meaning_en}</span>}
            </div>
            <p lang="nl" className="glossary-example muted">
              <SpokenText text={{ nl: item.example }} />
            </p>
            <button
              type="button"
              className="button secondary small"
              disabled={saved[item.term]}
              aria-pressed={saved[item.term] ?? false}
              onClick={() =>
                void stories
                  .saveWord(episodeId, item.term)
                  .then((result) => {
                    setSaved((current) => ({ ...current, [item.term]: true }));
                    setMessage(
                      fill(result.created ? episodeCopy.wordSaved : episodeCopy.wordKnown, {
                        term: item.term,
                      }),
                    );
                  })
                  .catch((cause) => setMessage(errorCopy(cause, episodeCopy.saveFailed)))
              }
            >
              <UiText text={saved[item.term] ? uiCopy.state.saved : uiCopy.action.save} inline />
            </button>
          </li>
        ))}
      </ul>
      {message && (
        <p className="practice-hint" role="status">
          <UiText text={message} tier="guide" />
        </p>
      )}
    </section>
  );
}

function Questions({ episode, onUpdate }: { episode: Episode; onUpdate: (episode: Episode) => void }) {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Copy | null>(null);
  const requestId = useRef(newRequestId());
  const complete = episode.questions.every((question) => answers[String(question.index)] !== undefined);
  const correct = episode.answered ? episode.questions.filter((question) => question.correct).length : 0;
  return (
    <section className="episode-questions" aria-labelledby="questions-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">
            <UiText text={episodeCopy.comprehension} />
          </p>
          <h2 id="questions-title">
            <UiText
              text={
                episode.answered
                  ? fill(episodeCopy.score, { correct, total: episode.questions.length })
                  : episode.questions.length === 2
                    ? episodeCopy.questionsTwo
                    : episodeCopy.questionsThree
              }
            />
          </h2>
        </div>
      </div>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (!complete || busy) return;
          setBusy(true);
          setMessage(null);
          void stories
            .answer(episode.id, answers, requestId.current)
            .then((updated) => {
              onUpdate(updated);
              const right = updated.questions.filter((question) => question.correct).length;
              playTone(right === updated.questions.length ? "correct" : "almost");
            })
            .catch((cause) => setMessage(errorCopy(cause, episodeCopy.answersFailed)))
            .finally(() => setBusy(false));
        }}
      >
        <ol className="question-list">
          {episode.questions.map((question) => (
            <li
              key={question.index}
              className={`episode-question ${episode.answered ? (question.correct ? "is-correct" : "is-wrong") : ""}`}
            >
              <p lang="nl" className="question-prompt">
                <SpokenText text={{ nl: question.prompt }} />
              </p>
              <div className="answer-options" role="radiogroup" aria-label={question.prompt}>
                {question.options.map((option, optionIndex) => (
                  <div key={optionIndex} className="answer-option-shell">
                    <label
                      className={episode.answered && question.answer_index === optionIndex ? "is-answer" : ""}
                    >
                      <input
                        type="radio"
                        name={`question-${question.index}`}
                        value={optionIndex}
                        disabled={episode.answered}
                        checked={
                          (episode.answered ? question.chosen : answers[String(question.index)]) ===
                          optionIndex
                        }
                        onChange={() =>
                          setAnswers((current) => ({ ...current, [String(question.index)]: optionIndex }))
                        }
                      />
                      <span lang="nl">{option}</span>
                    </label>
                    <SentenceAudio text={option} />
                  </div>
                ))}
              </div>
              {episode.answered && question.evidence && (
                <p className="question-evidence">
                  <Icon name={question.correct ? "check" : "help"} size={15} />{" "}
                  <span lang="nl">
                    <UiText text={episodeCopy.inTheStory} inline /> “{question.evidence}”
                  </span>
                </p>
              )}
            </li>
          ))}
        </ol>
        {!episode.answered && (
          <button className="button" type="submit" disabled={!complete || busy}>
            <UiText text={episodeCopy.checkAnswers} inline />
          </button>
        )}
        {message && (
          <p className="error" role="alert">
            <UiText text={message} tier="guide" />
          </p>
        )}
      </form>
    </section>
  );
}
