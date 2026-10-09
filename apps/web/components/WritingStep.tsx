"use client";

import { useEffect, useRef, useState } from "react";

import { WritingCoach } from "@/components/WritingCoach";
import { LearningText } from "@/components/LanguageSupport";
import { ContentLabel } from "@/components/ContentLabel";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { HelpLadder } from "@/components/HelpLadder";
import type { StepProps } from "@/components/ReadingStep";
import { StepHeader } from "@/components/StepHeader";
import { UiText } from "@/components/ui/UiText";
import { errorCopy } from "@/lib/client/error-copy";
import { DraftSaver } from "@/lib/client/draft-saver";
import { recordHelp, saveDraft, submitWriting } from "@/lib/client/practice";
import { missionsCopy } from "@/lib/copy/missions";
import type { HelpRung, Step, WritingPayload } from "@/lib/types";
import { fill, type Copy } from "@/lib/ui-copy";

interface Props extends StepProps {
  step: Step & { payload: WritingPayload };
}

const AUTOSAVE_MS = 1200;

export function countWords(text: string): number {
  return (text.match(/[\p{L}\p{N}'’-]+/gu) ?? []).length;
}

/**
 * The writing step: a message typed in Dutch. The draft autosaves into the session (not evidence);
 * the submitted message is stored as typed evidence with its word count and the required words found.
 */
export function WritingStep({
  step,
  labels,
  detail,
  ensureSession,
  onDetail,
  onProgressChanged,
  registerBeforeLeave,
}: Props) {
  const { payload } = step;
  const draft = detail?.drafts[step.key];
  const progress = detail?.session.step_progress[step.key];
  const [text, setText] = useState(draft?.text ?? "");
  const [savedAt, setSavedAt] = useState<string>(draft?.saved_at ?? "");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<Copy | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Copy | null>(null);
  const [error, setError] = useState<Copy | null>(null);
  const timerRef = useRef<number | null>(null);
  const textRef = useRef(text);
  const mountedRef = useRef(false);
  const persistRef = useRef<(text: string) => Promise<void>>(async () => {});
  const saverRef = useRef<DraftSaver | null>(null);
  // The autosave timer fires after later renders; it must merge into the newest detail, not the one it closed over.
  const detailRef = useRef(detail);
  useEffect(() => {
    detailRef.current = detail;
  }, [detail]);

  if (!saverRef.current) {
    saverRef.current = new DraftSaver(draft?.text ?? "", async (next) => {
      const current = detailRef.current ?? (await ensureSession());
      const saved = await saveDraft(current.session.id, step.key, next);
      const latest = detailRef.current ?? current;
      onDetail({ ...latest, drafts: { ...latest.drafts, [step.key]: saved } });
      if (mountedRef.current) setSavedAt(saved.saved_at);
    });
  }

  const words = countWords(text);
  const missing = payload.must_include.filter((item) => !text.toLowerCase().includes(item.toLowerCase()));
  const withinBounds = words >= payload.min_words && words <= payload.max_words;

  useEffect(() => {
    mountedRef.current = true;
    const warn = (event: BeforeUnloadEvent) => {
      if (!saverRef.current?.isSaved(textRef.current)) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    registerBeforeLeave?.(async () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
      try {
        await persistRef.current(textRef.current);
        return true;
      } catch {
        return false;
      }
    });
    return () => {
      mountedRef.current = false;
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
      window.removeEventListener("beforeunload", warn);
      registerBeforeLeave?.(null);
    };
  }, [registerBeforeLeave]);

  function scheduleSave(next: string) {
    if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => {
      timerRef.current = null;
      void persist(next).catch(() => undefined);
    }, AUTOSAVE_MS);
  }

  async function persist(next: string) {
    setSaving(true);
    setSaveError(null);
    try {
      await saverRef.current!.save(next);
    } catch (cause) {
      if (mountedRef.current) setSaveError(errorCopy(cause, missionsCopy.draftNotSaved, undefined, "input"));
      throw cause;
    } finally {
      if (mountedRef.current) setSaving(false);
    }
  }

  useEffect(() => {
    persistRef.current = persist;
  });

  async function submit() {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      // Drain older autosaves before submission so none can overwrite the submitted draft afterwards.
      await persist(text);
      const current = detailRef.current ?? (await ensureSession());
      const result = await submitWriting(current, step.key, text);
      onDetail(result.detail);
      onProgressChanged();
      setNotice(
        result.missing.length > 0
          ? fill(missionsCopy.submittedMissing, {
              count: result.word_count,
              missing: result.missing.join(", "),
            })
          : fill(
              payload.must_include.length ? missionsCopy.submittedComplete : missionsCopy.submittedReread,
              { count: result.word_count },
            ),
      );
    } catch (cause) {
      setError(errorCopy(cause, missionsCopy.submitFailed, undefined, "input"));
    } finally {
      setBusy(false);
    }
  }

  async function help(rung: HelpRung) {
    const current = detailRef.current ?? (await ensureSession());
    onDetail(await recordHelp(current, step.key, rung));
  }

  return (
    <article aria-labelledby="step-title" data-step={step.key} data-step-type="writing">
      <StepHeader step={step} labels={labels} />

      <section className="card" aria-labelledby="prompt-heading">
        <h3 id="prompt-heading">
          <UiText text={missionsCopy.assignment} />
        </h3>
        <p>
          <ContentLabel
            status={payload.prompt.review_status}
            labelNl={labels.unreviewed_nl}
            labelFa={labels.unreviewed_fa}
          />
        </p>
        <p>
          <LearningText text={payload.prompt} />
        </p>
        <p className="muted" style={{ fontSize: "0.85rem" }}>
          <UiText
            text={
              payload.must_include.length > 0
                ? fill(missionsCopy.wordRangeUse, {
                    min: payload.min_words,
                    max: payload.max_words,
                    words: payload.must_include.join(", "),
                  })
                : fill(missionsCopy.wordRange, { min: payload.min_words, max: payload.max_words })
            }
            inline
          />
        </p>
      </section>

      <section className="card" aria-labelledby="message-heading">
        <h3 id="message-heading">
          <UiText text={missionsCopy.yourMessage} />
        </h3>
        <label htmlFor={`writing-${step.key}`} className="visually-hidden">
          <UiText text={missionsCopy.messageLabel} />
        </label>
        <textarea
          id={`writing-${step.key}`}
          value={text}
          lang="nl"
          rows={8}
          maxLength={4000}
          disabled={busy}
          onChange={(event) => {
            textRef.current = event.target.value;
            setText(event.target.value);
            scheduleSave(event.target.value);
          }}
          onBlur={() => {
            if (timerRef.current !== null) window.clearTimeout(timerRef.current);
            void persist(text).catch(() => undefined);
          }}
          data-testid="writing-input"
          style={{ width: "100%", font: "inherit", padding: "0.6rem", lineHeight: 1.5 }}
        />
        <p className="status-line">
          <span data-testid="word-count" className={withinBounds ? "" : "muted"}>
            <UiText
              text={
                withinBounds
                  ? fill(missionsCopy.wordCount, { count: words })
                  : fill(missionsCopy.wordCountNeeded, {
                      count: words,
                      min: payload.min_words,
                      max: payload.max_words,
                    })
              }
              inline
            />
          </span>
          {missing.length > 0 ? (
            <span className="muted" data-testid="missing-words">
              <UiText text={fill(missionsCopy.stillToUse, { words: missing.join(", ") })} inline />
            </span>
          ) : (
            <span className="label ok">
              <UiText text={missionsCopy.allRequiredWords} inline />
            </span>
          )}
          <span className="muted" data-testid="autosave-status">
            {saveError ? (
              <UiText text={saveError} tier="guide" inline />
            ) : (
              <UiText
                text={
                  saving || !saverRef.current?.isSaved(text)
                    ? missionsCopy.autosaving
                    : savedAt
                      ? fill(missionsCopy.savedAt, {
                          time: new Date(savedAt).toLocaleTimeString("nl-BE", {
                            hour: "2-digit",
                            minute: "2-digit",
                          }),
                        })
                      : missionsCopy.notSavedYet
                }
                inline
              />
            )}
          </span>
        </p>
        {saveError && (
          <p role="alert">
            <button
              type="button"
              className="button secondary"
              onClick={() => void persist(text).catch(() => undefined)}
              disabled={saving}
            >
              <UiText text={missionsCopy.saveAgain} inline />
            </button>
            <span className="muted">
              {" "}
              <UiText text={missionsCopy.textStays} tier="guide" inline />
            </span>
          </p>
        )}
        <p>
          <button
            type="button"
            className="button"
            onClick={() => void submit()}
            disabled={busy || !withinBounds}
            data-testid="writing-submit"
          >
            <UiText
              text={
                busy
                  ? missionsCopy.submitting
                  : progress?.completed
                    ? missionsCopy.resubmit
                    : missionsCopy.submit
              }
              inline
            />
          </button>
          {progress?.completed && (
            <span className="label ok" style={{ marginInlineStart: "0.75rem" }} data-testid="writing-done">
              <UiText text={missionsCopy.messageSaved} inline />
            </span>
          )}
        </p>
        {notice && (
          <p role="status" data-testid="writing-notice">
            <UiText text={notice} tier="guide" />
          </p>
        )}
        {error && (
          <p className="error" role="alert">
            <UiText text={error} tier="guide" />
          </p>
        )}
      </section>

      <WritingCoach
        stageId="a2"
        text={text}
        disabled={busy}
        onApply={(value) => {
          textRef.current = value;
          setText(value);
          scheduleSave(value);
        }}
      />

      <section className="card" aria-labelledby="help-heading">
        <h3 id="help-heading">
          <UiText text={missionsCopy.help} />
        </h3>
        <HelpLadder rungs={payload.help} idPrefix={step.key} onReveal={help} />
      </section>

      <FeedbackPanel
        stepKey={step.key}
        detail={detail}
        onDetail={onDetail}
        onProgressChanged={onProgressChanged}
      />
    </article>
  );
}
