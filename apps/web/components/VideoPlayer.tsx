"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";
import { useLanguageSupport } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { failureText } from "@/components/VideoLibrary";
import { newRequestId } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { isAbort } from "@/lib/client/errors";
import { stageLabels, type GlossaryItem } from "@/lib/client/stories";
import { clock, sceneAt, videos, type Video } from "@/lib/client/videos";
import { Skeleton, SkeletonPanel } from "@/components/ui";
import { HonestyChip } from "@/components/ui/HonestyChip";
import { useDeveloperDetails } from "@/components/shell/EnvContext";
import { UiText } from "@/components/ui/UiText";
import { videoCopy } from "@/lib/copy/video";
import { fill, uiCopy, type Copy } from "@/lib/ui-copy";

export function VideoPlayer({ videoId }: { videoId: string }) {
  const developer = useDeveloperDetails();
  const [video, setVideo] = useState<Video | null>(null);
  const [error, setError] = useState<Copy | null>(null);
  const [time, setTime] = useState(0);
  const [finished, setFinished] = useState(false);
  const [showSubtitles, setShowSubtitles] = useState(true);
  const [notice, setNotice] = useState<Copy | null>(null);
  const player = useRef<HTMLVideoElement>(null);
  const load = useCallback(
    (signal?: AbortSignal) =>
      videos
        .get(videoId, signal)
        .then((value) => {
          setVideo(value);
          setFinished(Boolean(value.watched_at));
        })
        .catch((cause) => {
          if (!isAbort(cause))
            setError(errorCopy(cause, videoCopy.loadFailed, { 404: videoCopy.notFound }, "load"));
        }),
    [videoId],
  );
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);
  useEffect(() => {
    const element = player.current;
    if (!element) return;
    for (const track of Array.from(element.textTracks)) track.mode = showSubtitles ? "showing" : "hidden";
  }, [showSubtitles, video]);

  if (error)
    return (
      <div className="error" role="alert">
        <UiText text={error} tier="guide" inline />{" "}
        <Link href="/videos">
          <UiText text={videoCopy.backToVideos} inline />
        </Link>
      </div>
    );
  if (!video)
    return (
      <SkeletonPanel label={videoCopy.loading.nl}>
        <Skeleton lines={3} />
      </SkeletonPanel>
    );
  if (video.status !== "ready")
    return (
      <div className="card">
        <p className="eyebrow">
          {video.kind_label.toUpperCase()} · {stageLabels[video.stage_id] ?? video.stage_id}
        </p>
        <h1>
          <UiText text={video.status === "failed" ? videoCopy.failedTitle : videoCopy.makingTitle} />
        </h1>
        <p className="muted">
          {video.status === "failed" ? (
            <UiText text={failureText(video)} tier="guide" inline />
          ) : (
            <UiText text={videoCopy.makingBody} tier="guide" inline />
          )}{" "}
          {/* one sentence, so the gloss reads whole; the link covers it instead of "de video's" alone */}
          <Link href="/videos">
            <UiText text={videoCopy.checkStatus} tier="guide" inline />
          </Link>
        </p>
      </div>
    );

  const activeScene = sceneAt(video.cues, time);
  function seekTo(scene: number) {
    const cue = video?.cues.find((item) => item.scene === scene);
    const element = player.current;
    if (!cue || !element) return;
    element.currentTime = cue.start;
    setTime(cue.start);
    void element.play().catch(() => undefined);
  }
  const currentId = video.id;
  const presenter = video.presenter === "avatar" ? videoCopy.presenterAvatar : videoCopy.presenterCards;
  function markWatched() {
    if (finished) return;
    setFinished(true);
    void videos
      .watched(currentId)
      .then(setVideo)
      .catch((cause) => setNotice(errorCopy(cause, videoCopy.watchFailed)));
  }

  return (
    <article className="video-lesson" data-testid="video-lesson">
      <header className="video-lesson-header">
        <p className="eyebrow">
          {video.kind_label.toUpperCase()} · {stageLabels[video.stage_id] ?? video.stage_id} ·{" "}
          {clock(video.duration_seconds)} ·{" "}
          <UiText text={fill(videoCopy.wordCount, { count: video.word_count })} inline />
        </p>
        <h1>{video.title}</h1>
        <p className="muted">
          <UiText text={fill(videoCopy.topic, { topic: video.topic })} />
        </p>
      </header>

      <div className="video-stage">
        <video
          ref={player}
          controls
          playsInline
          preload="metadata"
          className="video-element"
          data-testid="video-element"
          onTimeUpdate={(event) => setTime(event.currentTarget.currentTime)}
          onSeeked={(event) => setTime(event.currentTarget.currentTime)}
          onEnded={markWatched}
        >
          <source src={`/api/${video.media_url}`} />
          <track
            kind="subtitles"
            src={`/api/${video.subtitles_url}`}
            srcLang="nl"
            label={videoCopy.subtitleTrack.nl}
            default
          />
          <UiText text={videoCopy.noVideoSupport} tier="guide" />
        </video>
        <div className="video-controls-row">
          <label className="toggle">
            <input
              type="checkbox"
              checked={showSubtitles}
              onChange={(event) => setShowSubtitles(event.target.checked)}
            />{" "}
            <UiText text={videoCopy.subtitles} inline />
          </label>
          <span className="small-text muted">
            <UiText text={presenter} tier="guide" inline />
            {developer && <span className="muted"> ({video.voice || video.renderer})</span>}
          </span>
        </div>
      </div>

      <Transcript video={video} activeScene={activeScene} onSeek={seekTo} />

      <Glossary videoId={video.id} items={video.glossary} />

      {!finished && (
        <div className="finish-row">
          <button className="button" data-testid="finish-watching" onClick={markWatched}>
            <UiText text={videoCopy.finishWatching} inline />
            <Icon name="arrow" size={18} />
          </button>
          <span className="small-text muted">
            <UiText text={videoCopy.questionsFollow} tier="guide" inline />
          </span>
        </div>
      )}

      {finished && (
        <>
          <Questions video={video} onUpdate={setVideo} />
          <footer className="episode-footer">
            <div className="rating" role="group" aria-label={videoCopy.ratingGroup.nl}>
              <span className="small-text muted">
                <UiText text={videoCopy.ratingPrompt} inline />
              </span>
              <button
                type="button"
                className={`linklike ${video.rating === 1 ? "is-on" : ""}`}
                aria-pressed={video.rating === 1}
                onClick={() =>
                  void videos
                    .rate(video.id, 1)
                    .then(setVideo)
                    .catch(() => undefined)
                }
              >
                <UiText text={videoCopy.ratingYes} inline />
              </button>
              <button
                type="button"
                className={`linklike ${video.rating === -1 ? "is-on" : ""}`}
                aria-pressed={video.rating === -1}
                onClick={() =>
                  void videos
                    .rate(video.id, -1)
                    .then(setVideo)
                    .catch(() => undefined)
                }
              >
                <UiText text={videoCopy.ratingNo} inline />
              </button>
            </div>
            <Link className="stage-link" href="/videos">
              <UiText text={videoCopy.anotherVideo} inline />
              <Icon name="arrow" size={17} />
            </Link>
            <div className="honesty-row">
              <HonestyChip
                kind="video"
                detail={`${video.model || video.provider}; automatische controle: ${video.warnings.length} aandachtspunten`}
              />
            </div>
            {notice && (
              <p className="error" role="alert">
                <UiText text={notice} tier="guide" />
              </p>
            )}
          </footer>
        </>
      )}
      {!finished && notice && (
        <p className="error" role="alert">
          <UiText text={notice} tier="guide" />
        </p>
      )}
    </article>
  );
}

function Transcript({
  video,
  activeScene,
  onSeek,
}: {
  video: Video;
  activeScene: number;
  onSeek: (scene: number) => void;
}) {
  const { showEnglish, showPersian } = useLanguageSupport();
  return (
    <section className="video-transcript" aria-labelledby="transcript-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">
            <UiText text={videoCopy.transcriptEyebrow} />
          </p>
          <h2 id="transcript-title">
            <UiText text={videoCopy.readAlong} />
          </h2>
        </div>
        <span className="small-text muted">
          <UiText text={videoCopy.sceneHint} tier="guide" />
        </span>
      </div>
      <ol className="scene-list">
        {video.scenes.map((scene, index) => (
          <li
            key={index}
            className={`scene ${index === activeScene ? "is-active" : ""}`}
            data-testid="video-scene"
            aria-current={index === activeScene ? "true" : undefined}
          >
            <button
              type="button"
              className="scene-jump"
              onClick={() => onSeek(index)}
              aria-label={fill(videoCopy.goToScene, { number: index + 1 }).nl}
            >
              <span className="scene-keyword" lang="nl">
                {scene.keyword}
              </span>
            </button>
            <div className="scene-text">
              <p lang="nl" className="story-copy">
                {scene.nl}{" "}
                <PhraseAudio text={scene.nl} label={fill(videoCopy.sceneName, { number: index + 1 }).nl} />
              </p>
              {showEnglish && scene.en && (
                <p lang="en" className="copy-support">
                  {scene.en}
                </p>
              )}
              {showPersian && scene.fa && (
                <p lang="fa" dir="rtl" className="copy-support fa">
                  {scene.fa}
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Glossary({ videoId, items }: { videoId: string; items: GlossaryItem[] }) {
  const { showEnglish, showPersian } = useLanguageSupport();
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState<Copy | null>(null);
  if (!items.length) return null;
  return (
    <section className="episode-glossary" aria-labelledby="video-glossary-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">
            <UiText text={videoCopy.newWordsEyebrow} />
          </p>
          <h2 id="video-glossary-title">
            <UiText text={videoCopy.glossaryTitle} />
          </h2>
        </div>
        <span className="quiet-badge">
          <UiText text={fill(videoCopy.glossaryCount, { count: items.length })} inline />
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
              {item.example}
            </p>
            <button
              type="button"
              className="button secondary small"
              disabled={saved[item.term]}
              aria-pressed={saved[item.term] ?? false}
              onClick={() =>
                void videos
                  .saveWord(videoId, item.term)
                  .then((result) => {
                    setSaved((current) => ({ ...current, [item.term]: true }));
                    setMessage(
                      fill(result.created ? videoCopy.wordSaved : videoCopy.wordKnown, { term: item.term }),
                    );
                  })
                  .catch((cause) => setMessage(errorCopy(cause, videoCopy.saveFailed)))
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

function Questions({ video, onUpdate }: { video: Video; onUpdate: (video: Video) => void }) {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Copy | null>(null);
  const requestId = useRef(newRequestId());
  const complete = video.questions.every((question) => answers[String(question.index)] !== undefined);
  const correct = video.answered ? video.questions.filter((question) => question.correct).length : 0;
  return (
    <section className="episode-questions" aria-labelledby="video-questions-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">
            <UiText text={videoCopy.comprehensionEyebrow} />
          </p>
          <h2 id="video-questions-title">
            <UiText
              text={
                video.answered
                  ? fill(videoCopy.score, { correct, total: video.questions.length })
                  : video.questions.length === 2
                    ? videoCopy.questionsTwo
                    : videoCopy.questionsThree
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
          void videos
            .answer(video.id, answers, requestId.current)
            .then(onUpdate)
            .catch((cause) => setMessage(errorCopy(cause, videoCopy.answersFailed)))
            .finally(() => setBusy(false));
        }}
      >
        <ol className="question-list">
          {video.questions.map((question) => (
            <li
              key={question.index}
              className={`episode-question ${video.answered ? (question.correct ? "is-correct" : "is-wrong") : ""}`}
            >
              <p lang="nl" className="question-prompt">
                {question.prompt}
              </p>
              <div className="answer-options" role="radiogroup" aria-label={question.prompt}>
                {question.options.map((option, optionIndex) => (
                  <label
                    key={optionIndex}
                    className={video.answered && question.answer_index === optionIndex ? "is-answer" : ""}
                  >
                    <input
                      type="radio"
                      name={`video-question-${question.index}`}
                      value={optionIndex}
                      disabled={video.answered}
                      checked={
                        (video.answered ? question.chosen : answers[String(question.index)]) === optionIndex
                      }
                      onChange={() =>
                        setAnswers((current) => ({ ...current, [String(question.index)]: optionIndex }))
                      }
                    />
                    <span lang="nl">{option}</span>
                  </label>
                ))}
              </div>
              {video.answered && question.evidence && (
                <p className="question-evidence">
                  <Icon name={question.correct ? "check" : "help"} size={15} />{" "}
                  <span lang="nl">
                    <UiText
                      text={fill(videoCopy.evidence, { evidence: question.evidence })}
                      tier="guide"
                      inline
                    />
                  </span>
                </p>
              )}
            </li>
          ))}
        </ol>
        {!video.answered && (
          <button className="button" type="submit" disabled={!complete || busy}>
            <UiText text={videoCopy.checkAnswers} inline />
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
