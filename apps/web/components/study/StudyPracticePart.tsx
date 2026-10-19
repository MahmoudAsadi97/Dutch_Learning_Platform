"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { SpokenText } from "@/components/SpokenPassage";
import { apiFetch, apiJson, ApiError } from "@/lib/client/api";
import { friendlyError } from "@/lib/client/curriculum";
import { STOP_TAIL_MS, useRecorder, type Recording } from "@/lib/client/recorder";
import { useNavigationGuard } from "@/lib/client/navigation";
import { observeNativeAudioFocus } from "@/lib/client/audio-focus";
import type { StudyFeedback, StudyLesson, StudyPart, StudyStep } from "@/lib/client/study";
import {
  studyCopy,
  studyLabels,
  studyDimensions,
  studyReviewComparison,
  studySemanticReviewCopy,
} from "@/lib/copy/study";
import { StudyError } from "./StudyShared";

export function PracticePart({
  lesson,
  part,
  mode,
  assisted,
  onAssisted,
  onNext,
}: {
  lesson: StudyLesson;
  part: StudyPart;
  mode: StudyStep;
  assisted: boolean;
  onAssisted: () => void;
  onNext: () => void;
}) {
  const [text, setText] = useState("");
  const [answers, setAnswers] = useState<Record<string, string | number>>({});
  const [feedback, setFeedback] = useState<StudyFeedback | null>(null);
  const [reviewedQuestionId, setReviewedQuestionId] = useState<string | null>(null);
  const questionReviewPending = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sample, setSample] = useState(false);
  const [transcript, setTranscript] = useState(false);
  const [audioUrl, setAudioUrl] = useState("");
  const [voiceUrl, setVoiceUrl] = useState("");
  const [audioBusy, setAudioBusy] = useState(false);
  const [syntheticTest, setSyntheticTest] = useState(false);
  const [questionIndex, setQuestionIndex] = useState(() =>
    mode === "check" && lesson.skill === "speaking" && part.practice_questions?.length
      ? Math.floor(Math.random() * part.practice_questions.length)
      : 0,
  );
  const controller = useRef<AbortController | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const localAudio = useRef("");
  const localVoice = useRef("");
  const mounted = useRef(true);

  const question = part.practice_questions?.[questionIndex];
  const prompt = question?.prompt ?? part.prompt;
  const example = question?.sample ?? part.sample;
  const objective = part.questions.length > 0;
  const isSpeaking = lesson.skill === "speaking" || (lesson.skill === "reading" && part.id === "retell");
  const registerGuard = useNavigationGuard();
  const onRecording = useCallback(
    async (recording: Recording) => {
      if (localVoice.current) URL.revokeObjectURL(localVoice.current);
      localVoice.current = URL.createObjectURL(recording.blob);
      setVoiceUrl(localVoice.current);
      setBusy(true);
      setError("");
      setFeedback(null);
      const request = new AbortController();
      controller.current?.abort();
      controller.current = request;
      const body = new FormData();
      body.append("audio", recording.blob, recording.fileName);
      try {
        const value = await apiJson<{ transcript: { text: string }; evidence?: unknown }>(
          `study/${lesson.stage_id}/topics/${lesson.topic_id}/transcribe`,
          { method: "POST", formData: body, signal: request.signal },
        );
        if (mounted.current && controller.current === request && !request.signal.aborted)
          setText(value.transcript.text);
      } catch (cause) {
        if (mounted.current && !(cause instanceof DOMException && cause.name === "AbortError"))
          setError(friendlyError(cause));
      } finally {
        if (mounted.current && controller.current === request) setBusy(false);
      }
    },
    [lesson.stage_id, lesson.topic_id],
  );
  const recorder = useRecorder(onRecording);
  const stopRecording = recorder.stop;
  const recording = recorder.phase === "recording";
  useEffect(() => {
    mounted.current = true;
    const stopObserving = observeNativeAudioFocus();
    return () => {
      mounted.current = false;
      controller.current?.abort();
      stopObserving();
      if (localAudio.current) URL.revokeObjectURL(localAudio.current);
      if (localVoice.current) URL.revokeObjectURL(localVoice.current);
    };
  }, []);
  useEffect(() => {
    registerGuard(async () => {
      if (recording || busy) {
        setError(recording ? studyCopy.stopBeforeLeaving.nl : studyCopy.waitBeforeLeaving.nl);
        return false;
      }
      return true;
    });
    return () => registerGuard(null);
  }, [registerGuard, recording, busy]);
  useEffect(() => {
    if (!recording) return;
    const timer = window.setTimeout(
      () => stopRecording(),
      Math.max(1000, (lesson.policy.recording_max_seconds ?? 60) * 1000 - STOP_TAIL_MS - 600),
    );
    return () => window.clearTimeout(timer);
  }, [recording, stopRecording, lesson.policy.recording_max_seconds]);
  useEffect(() => {
    const clear = (event: PageTransitionEvent) => {
      if (event.persisted) {
        setText("");
        setAnswers({});
        setFeedback(null);
        setSample(false);
        setTranscript(false);
        setVoiceUrl("");
      }
    };
    window.addEventListener("pageshow", clear);
    return () => window.removeEventListener("pageshow", clear);
  }, []);
  async function playListening() {
    setAudioBusy(true);
    setError("");
    try {
      if (!localAudio.current) {
        const response = await apiFetch(
          `study/${lesson.stage_id}/topics/${lesson.topic_id}/audio?${new URLSearchParams({ skill: lesson.skill, activity_id: lesson.activity_id, part: part.id })}`,
          { method: "POST" },
        );
        if (!response.ok) throw new ApiError(response.status, "", "");
        localAudio.current = URL.createObjectURL(await response.blob());
        if (!mounted.current) {
          URL.revokeObjectURL(localAudio.current);
          return;
        }
        setSyntheticTest((response.headers.get("x-audio-label") ?? "").includes("test"));
        setAudioUrl(localAudio.current);
        if (audioRef.current) {
          audioRef.current.src = localAudio.current;
          audioRef.current.load();
        }
      }
      await audioRef.current?.play();
    } catch (cause) {
      if (mounted.current)
        setError(
          cause instanceof DOMException && cause.name === "NotAllowedError"
            ? studyCopy.tapPlayAgain.nl
            : friendlyError(cause),
        );
    } finally {
      if (mounted.current) setAudioBusy(false);
    }
  }
  async function evaluate() {
    setBusy(true);
    setError("");
    setReviewedQuestionId(null);
    const request = new AbortController();
    controller.current = request;
    try {
      const value = await apiJson<StudyFeedback>(
        `study/${lesson.stage_id}/topics/${lesson.topic_id}/feedback`,
        {
          method: "POST",
          signal: request.signal,
          body: {
            skill: lesson.skill,
            activity_id: lesson.activity_id,
            part: part.id,
            kind: objective ? "answers" : "response",
            text,
            answers,
            assistance_used: assisted || sample || transcript,
            ...(question ? { question_id: question.id } : {}),
          },
        },
      );
      if (mounted.current && controller.current === request && !request.signal.aborted) setFeedback(value);
    } catch (cause) {
      if (mounted.current && !(cause instanceof DOMException && cause.name === "AbortError"))
        setError(friendlyError(cause));
    } finally {
      if (mounted.current && controller.current === request) setBusy(false);
    }
  }
  async function evaluateQuestion(questionId: string) {
    const answer = String(answers[questionId] ?? "").trim();
    const item = part.questions.find((candidate) => candidate.id === questionId);
    if (busy || recording || questionReviewPending.current || !answer || !item || item.kind === "choice")
      return;
    questionReviewPending.current = true;
    setBusy(true);
    setError("");
    const request = new AbortController();
    controller.current?.abort();
    controller.current = request;
    try {
      const value = await apiJson<StudyFeedback>(
        `study/${lesson.stage_id}/topics/${lesson.topic_id}/feedback`,
        {
          method: "POST",
          signal: request.signal,
          body: {
            skill: lesson.skill,
            activity_id: lesson.activity_id,
            part: part.id,
            kind: "response",
            question_id: questionId,
            text: answer,
            assistance_used: assisted || sample || transcript,
          },
        },
      );
      if (mounted.current && controller.current === request && !request.signal.aborted) {
        setReviewedQuestionId(questionId);
        setFeedback(value);
      }
    } catch (cause) {
      if (mounted.current && controller.current === request && !request.signal.aborted)
        setError(friendlyError(cause));
    } finally {
      questionReviewPending.current = false;
      if (mounted.current && controller.current === request) setBusy(false);
    }
  }
  function invalidateFeedback() {
    controller.current?.abort();
    controller.current = null;
    setFeedback(null);
    setReviewedQuestionId(null);
    setError("");
    setBusy(false);
  }
  function clearQuestionMedia() {
    if (localVoice.current) URL.revokeObjectURL(localVoice.current);
    if (localAudio.current) URL.revokeObjectURL(localAudio.current);
    localVoice.current = "";
    localAudio.current = "";
    audioRef.current?.pause();
    setVoiceUrl("");
    setAudioUrl("");
  }
  const canCheck = objective
    ? part.questions.every((item) => answers[item.id] !== undefined && String(answers[item.id]).trim() !== "")
    : text.trim().length > 0;
  return (
    <div className="study-practice" data-testid="study-practice">
      <div className="study-task-heading">
        <h2>
          <LearningText text={part.title} />
        </h2>
        <p>
          <LearningText text={part.instructions} />
        </p>
      </div>
      {(lesson.skill === "speaking" || lesson.skill === "writing") && lesson.context && (
        <details className="study-context">
          <summary>
            {" "}
            <LearningText text={studyCopy.context} />{" "}
          </summary>
          <h3>
            <LearningText text={lesson.context.title} />
          </h3>
          {lesson.context.text.map((line, index) => (
            <SpokenText key={index} text={line} />
          ))}
        </details>
      )}
      {(lesson.skill === "speaking" || lesson.skill === "writing") && (
        <p className="study-quiet">
          {" "}
          <LearningText text={studyCopy.fictionalAnswer} />{" "}
        </p>
      )}
      {lesson.skill === "listening" && part.text.length > 0 && (
        <section className="study-listen-player">
          <div>
            <span className="study-skill-icon">
              <Icon name="headphones" size={22} />
            </span>
            <div>
              <strong>
                {" "}
                <LearningText text={studyCopy.listenSituation} />{" "}
              </strong>
              <p>
                {" "}
                <LearningText text={studyCopy.listenInstructions} />{" "}
              </p>
            </div>
          </div>
          <button
            className="button"
            disabled={audioBusy || recording || busy}
            onClick={() => void playListening()}
          >
            <Icon name="play" size={17} />
            {audioBusy ? studyCopy.prepareAudio.nl : studyCopy.startRecordingAudio.nl}
          </button>
          <audio
            ref={audioRef}
            controls
            preload="none"
            src={audioUrl || undefined}
            aria-label={studyCopy.continuousAudio.nl}
          />
          {syntheticTest && (
            <p className="study-footnote">
              {" "}
              <LearningText text={studyCopy.testAudio} />{" "}
            </p>
          )}
          <details
            open={transcript}
            onToggle={(event) => {
              const open = event.currentTarget.open;
              setTranscript(open);
              if (open) onAssisted();
            }}
          >
            <summary>
              {" "}
              <LearningText text={studyCopy.revealTranscript} />{" "}
            </summary>
            {part.text.map((line, index) => (
              <p key={index}>
                <SpokenText text={line} />
              </p>
            ))}
          </details>
        </section>
      )}
      {lesson.skill !== "listening" && part.text.length > 0 && (
        <article className="study-story" aria-label={studyCopy.story.nl}>
          <div className="study-story-lines">
            {part.text.map((line, index) => (
              <p
                className="study-story-line"
                data-paragraph-start={
                  part.text.length >= 8 && index === Math.ceil(part.text.length / 2) ? "" : undefined
                }
                key={index}
              >
                <span className="study-line-number" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <SpokenText text={line} />
              </p>
            ))}
          </div>
        </article>
      )}
      {!objective && (
        <div className="study-response-prompt">
          <SpokenText text={prompt} />
        </div>
      )}
      {part.practice_questions && part.practice_questions.length > 1 && (
        <button
          className="study-text-button"
          disabled={busy || recording}
          onClick={() => {
            setQuestionIndex(
              (value) =>
                (value + 1 + Math.floor(Math.random() * (part.practice_questions!.length - 1))) %
                part.practice_questions!.length,
            );
            clearQuestionMedia();
            setText("");
            setAnswers({});
            invalidateFeedback();
            setSample(false);
            setTranscript(false);
          }}
        >
          <LearningText text={studyCopy.anotherShortQuestion} /> <Icon name="refresh" size={15} />
        </button>
      )}
      {example && (
        <div className="study-example">
          <button
            className="study-text-button"
            aria-expanded={sample}
            onClick={() => {
              setSample(!sample);
              onAssisted();
            }}
          >
            <Icon name={sample ? "eye-off" : "lightbulb"} size={17} />
            <LearningText text={studyLabels.example(sample)} />
          </button>
          {sample && (
            <div className="study-example-answer">
              <SpokenText text={example} />
              <p className="study-footnote">
                {" "}
                <LearningText text={studyCopy.exampleHelp} />{" "}
              </p>
            </div>
          )}
        </div>
      )}
      {objective ? (
        <div className="study-questions">
          {part.questions.map((item, index) => (
            <fieldset key={item.id} className="study-question" disabled={busy}>
              <legend>
                <span>{index + 1}.</span> <LearningText text={item.prompt} />
              </legend>
              <PhraseAudio text={item.prompt.nl} />
              {item.kind === "choice" ? (
                <div className="study-answer-options">
                  {item.options.map((option, position) => (
                    <div className="study-option" key={position}>
                      <label>
                        <input
                          type="radio"
                          name={item.id}
                          checked={answers[item.id] === position}
                          onChange={() => {
                            setAnswers((value) => ({ ...value, [item.id]: position }));
                            invalidateFeedback();
                          }}
                        />
                        <span lang="nl">{option.nl}</span>
                      </label>
                      <PhraseAudio text={option.nl} />
                    </div>
                  ))}
                </div>
              ) : (
                <input
                  aria-label={studyLabels.questionAnswer(index + 1)}
                  value={String(answers[item.id] ?? "")}
                  onChange={(event) => {
                    setAnswers((value) => ({ ...value, [item.id]: event.target.value }));
                    invalidateFeedback();
                  }}
                  maxLength={300}
                  autoComplete="off"
                  placeholder={item.kind === "gap" ? studyCopy.fillGap.nl : studyCopy.shortAnswer.nl}
                />
              )}
            </fieldset>
          ))}
        </div>
      ) : (
        <div className="study-response">
          {isSpeaking && (
            <div className="study-recorder">
              <p className="study-footnote">
                <LearningText text={studyLabels.recordingLimit(lesson.policy.recording_max_seconds ?? 60)} />
              </p>
              <button
                type="button"
                className={`study-record-button ${recording ? "is-recording" : ""}`}
                aria-pressed={recording}
                disabled={busy || recorder.phase === "unsupported"}
                onClick={() => (recording ? recorder.stop() : void recorder.start())}
              >
                <Icon name={recording ? "pause" : "mic"} size={23} />
                {recording ? studyCopy.stopRecording.nl : studyCopy.recordAnswer.nl}
              </button>
              <span>{recording ? studyCopy.microphoneOn.nl : studyCopy.recordingPrivate.nl}</span>
              {voiceUrl && <audio controls src={voiceUrl} aria-label={studyCopy.playOwnRecording.nl} />}
              {recorder.error && <p role="alert">{recorder.error}</p>}
            </div>
          )}
          <label htmlFor="study-response-text">
            <LearningText text={studyLabels.response(isSpeaking)} />
          </label>
          <textarea
            id="study-response-text"
            value={text}
            onChange={(event) => {
              setText(event.target.value);
              invalidateFeedback();
            }}
            rows={isSpeaking ? 4 : 7}
            maxLength={8000}
            disabled={busy || recording}
            placeholder={isSpeaking ? studyCopy.speechPlaceholder.nl : studyCopy.writingPlaceholder.nl}
            spellCheck
            lang="nl-BE"
          />
          <div className="study-response-meta">
            <span>
              {text.trim() ? text.trim().split(/\s+/).length : 0} <LearningText text={studyCopy.words} />{" "}
            </span>
            <span>
              <LearningText text={studyLabels.wordGuideline(part.min_words, part.max_words)} />
            </span>
          </div>
        </div>
      )}
      {error && <StudyError message={error} />}
      <div className="study-check-actions">
        <button className="button" disabled={!canCheck || busy || recording} onClick={() => void evaluate()}>
          <Icon name="check" size={17} />
          <LearningText text={studyLabels.review(busy)} />
        </button>
        {mode === "practise" && (
          <button className="button secondary" disabled={busy || recording} onClick={onNext}>
            <LearningText text={studyCopy.nextPart} /> <Icon name="arrow" size={16} />
          </button>
        )}
      </div>
      {feedback && (
        <section className="study-feedback" aria-label={studyCopy.temporaryFeedback.nl} aria-live="polite">
          <div className="study-feedback-heading">
            <div>
              <p className="study-kicker">
                {" "}
                <LearningText text={studyCopy.feedbackKicker} />{" "}
              </p>
              <h3>
                {reviewedQuestionId ? (
                  <LearningText
                    text={studyLabels.questionFeedback(
                      part.questions.findIndex((item) => item.id === reviewedQuestionId) + 1,
                    )}
                  />
                ) : (
                  <LearningText text={objective ? studyCopy.understandingTitle : studyCopy.clearerAnswer} />
                )}
              </h3>
            </div>
            {feedback.score !== null ? (
              <span className="study-score">
                {feedback.score}
                <small>/10</small>
              </span>
            ) : (
              <span className="study-score-pending">
                {" "}
                <LearningText text={studyCopy.noReliableScore} />{" "}
              </span>
            )}
          </div>
          {reviewedQuestionId && (
            <p className="study-footnote">
              <LearningText text={studySemanticReviewCopy.scope} />
            </p>
          )}
          <p>
            <LearningText text={feedback.summary} />
          </p>
          {!objective && (
            <div className="study-dimension-grid">
              {(["task", "grammar", "vocabulary", "organisation"] as const).map((key) => (
                <div key={key}>
                  <span>
                    <LearningText text={studyDimensions[key]} />
                  </span>
                  <strong>
                    {feedback.dimensions[key] === null ? "—" : `${feedback.dimensions[key]}/10`}
                  </strong>
                </div>
              ))}
            </div>
          )}
          {feedback.checks.map((check) => (
            <div
              className={`study-answer-review ${check.correct === true ? "is-correct" : check.correct === null ? "is-neutral" : ""}`}
              key={check.id}
            >
              <Icon name={check.correct === true ? "check" : "lightbulb"} size={18} />
              <div>
                <strong>
                  {check.correct === null ? (
                    <LearningText text={studyReviewComparison} />
                  ) : (
                    <LearningText text={check.correct ? studyCopy.wellUnderstood : studyCopy.reviewAgain} />
                  )}
                </strong>
                <p>
                  <SpokenText text={check.answer} />
                </p>
                <LearningText text={check.explanation} />
                {(check.correct === null || check.review_required) &&
                  part.questions.some((item) => item.id === check.id && item.kind !== "choice") && (
                    <div className="study-question-review-action">
                      <p className="study-footnote">
                        <LearningText text={studySemanticReviewCopy.explanation} />
                      </p>
                      <button
                        type="button"
                        className="button secondary"
                        disabled={busy || recording || !String(answers[check.id] ?? "").trim()}
                        onClick={() => void evaluateQuestion(check.id)}
                      >
                        <Icon name="check" size={16} />
                        <LearningText text={studySemanticReviewCopy.action} />
                      </button>
                    </div>
                  )}
              </div>
            </div>
          ))}
          {feedback.corrections.map((correction, index) => (
            <div className="study-correction" key={index}>
              <div>
                <del lang="nl">{correction.original}</del>
                <Icon name="arrow" size={16} />
                <strong lang="nl">{correction.replacement}</strong>
                <PhraseAudio text={correction.replacement} />
              </div>
              <p>
                <LearningText text={correction.explanation} />
              </p>
            </div>
          ))}
          {isSpeaking && (
            <p className="study-footnote">
              <LearningText text={feedback.pronunciation_note} />
            </p>
          )}
          <p className="study-footnote">
            <LearningText text={studyCopy.practiceDisclaimer} />
          </p>
          <button
            className="button secondary"
            onClick={() => {
              setFeedback(null);
              setSample(false);
            }}
          >
            <LearningText text={studyCopy.reviseAnswer} /> <Icon name="pen" size={16} />
          </button>
        </section>
      )}
    </div>
  );
}
